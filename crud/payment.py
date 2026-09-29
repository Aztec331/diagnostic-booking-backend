from sqlalchemy.orm import Session

from models.booking import Booking
from models.payment import Payment
from models.payment_event import PaymentEvent

def get_booking(db: Session, booking_id: int):
    return db.query(Booking).filter(
        Booking.id == booking_id
    ).first()


def create_payment(
    db: Session,
    booking_id: int,
    amount,
    status: str,
):
    payment = Payment(
        booking_id=booking_id,
        amount=amount,
        status=status,
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment

def get_payment_event(db: Session, event_id: str):
    return db.query(PaymentEvent).filter(
        PaymentEvent.event_id == event_id
    ).first()

def get_payment(db: Session, payment_id: int):
    return db.query(Payment).filter(
        Payment.id == payment_id
    ).first()

def get_payment_by_booking(db: Session, booking_id: int):
    return db.query(Payment).filter(
        Payment.booking_id == booking_id
    ).first()