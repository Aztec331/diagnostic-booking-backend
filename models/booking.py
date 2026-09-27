from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    Numeric,
    DateTime,
    String,
    UniqueConstraint,
)
from database import Base


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    centre_id = Column(
        Integer,
        ForeignKey("diagnostic_centres.id"),
        nullable=False
    )

    test_id = Column(
        Integer,
        ForeignKey("diagnostic_tests.id"),
        nullable=False
    )

    appointment_at = Column(DateTime, nullable=False)

    amount = Column(Numeric(10, 2), nullable=False)

    status = Column(
        String,
        nullable=False,
        default="PENDING"
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "centre_id",
            "test_id",
            "appointment_at",
            name="uq_duplicate_booking"
        ),
    )
