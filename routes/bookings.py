from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.dependencies import get_current_user
from crud.booking import (
    create_booking,
    get_centre_test,
    get_user_bookings,
    get_booking_by_id,
)
from database import get_db
from models.user import User
from schemas.booking import BookingCreate


router = APIRouter(
    prefix="/api/bookings",
    tags=["Bookings"],
)


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_new_booking(
    booking_data: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    centre_test = get_centre_test(
        db=db,
        centre_id=booking_data.centre_id,
        test_id=booking_data.test_id,
    )

    if not centre_test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test is not available at this diagnostic centre",
        )

    booking = create_booking(
        db=db,
        user_id=current_user.id,
        centre_id=booking_data.centre_id,
        test_id=booking_data.test_id,
        appointment_at=booking_data.appointment_at,
        amount=centre_test.price,
    )

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Booking already exists for this appointment",
        )

    return {
        "id": booking.id,
        "user_id": booking.user_id,
        "centre_id": booking.centre_id,
        "test_id": booking.test_id,
        "appointment_at": booking.appointment_at,
        "amount": booking.amount,
        "status": booking.status,
    }

@router.get("/")
def get_my_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bookings = get_user_bookings(
        db=db,
        user_id=current_user.id,
    )

    response = []

    for booking in bookings:
        response.append({
            "id": booking.id,
            "user_id": booking.user_id,
            "centre_id": booking.centre_id,
            "test_id": booking.test_id,
            "appointment_at": booking.appointment_at,
            "amount": booking.amount,
            "status": booking.status,
        })

    return response

@router.get("/{booking_id}")
def get_my_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = get_booking_by_id(
        db=db,
        booking_id=booking_id,
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

    return {
        "id": booking.id,
        "user_id": booking.user_id,
        "centre_id": booking.centre_id,
        "test_id": booking.test_id,
        "appointment_at": booking.appointment_at,
        "amount": booking.amount,
        "status": booking.status,
    }