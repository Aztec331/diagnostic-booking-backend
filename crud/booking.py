from sqlalchemy.orm import Session
from models.booking import Booking
from models.centre_test import CentreTest
from sqlalchemy.exc import IntegrityError

def create_booking(
    db: Session,
    user_id: int,
    centre_id: int,
    test_id: int,
    appointment_at,
    amount,
):
    booking = Booking(
        user_id=user_id,
        centre_id=centre_id,
        test_id=test_id,
        appointment_at=appointment_at,
        amount=amount,
        status="PENDING",
    )

    db.add(booking)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return None

    db.refresh(booking)
    return booking

def get_centre_test(db: Session, centre_id: int, test_id: int):
    return db.query(CentreTest).filter(
        CentreTest.centre_id == centre_id,
        CentreTest.test_id == test_id,
    ).first()

def get_user_bookings(db: Session, user_id: int):
    return db.query(Booking).filter(
        Booking.user_id == user_id
    ).all()

def get_booking_by_id(db: Session, booking_id: int):
    return db.query(Booking).filter(
        Booking.id == booking_id
    ).first()