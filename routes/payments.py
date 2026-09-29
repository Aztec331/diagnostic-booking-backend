from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.dependencies import get_current_user
from crud.payment import (
    get_booking,
    create_payment,
    get_payment_event,
    get_payment,
    get_payment_by_booking,
)
from database import get_db
from models.user import User
from models.payment_event import PaymentEvent
from schemas.payment import PaymentCreate, PaymentWebhook


router = APIRouter(
    prefix="/api/payments",
    tags=["Payments"],
)


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_new_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = get_booking(
        db=db,
        booking_id=payment_data.booking_id,
    )

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    if booking.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    if booking.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending bookings can be paid",
        )

    existing_payment = get_payment_by_booking(
    db=db,
    booking_id=booking.id,
    )

    if existing_payment:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment already exists for this booking",
        )

    payment = create_payment(
        db=db,
        booking_id=booking.id,
        amount=booking.amount,
        status="PENDING",
    )

    return {
        "id": payment.id,
        "booking_id": payment.booking_id,
        "amount": payment.amount,
        "status": payment.status,
    }

@router.post("/webhook/")
def payment_webhook(
    webhook_data: PaymentWebhook,
    db: Session = Depends(get_db),
):
    existing_event = get_payment_event(
        db=db,
        event_id=webhook_data.event_id,
    )

    if existing_event:
        return {
            "message": "Event already processed"
        }

    payment = get_payment(
        db=db,
        payment_id=webhook_data.payment_id,
    )

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    booking = get_booking(
        db=db,
        booking_id=payment.booking_id,
    )

    payment.status = webhook_data.event_type

    if webhook_data.event_type == "SUCCESS":
        booking.status = "CONFIRMED"

    elif webhook_data.event_type == "FAILED":
        booking.status = "FAILED"

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment event type",
        )

    event = PaymentEvent(
        payment_id=payment.id,
        event_id=webhook_data.event_id,
        event_type=webhook_data.event_type,
    )

    db.add(event)
    db.commit()

    return {
        "message": "Payment updated successfully",
        "payment_id": payment.id,
        "payment_status": payment.status,
        "booking_status": booking.status,
    }