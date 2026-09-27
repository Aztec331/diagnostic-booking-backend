from sqlalchemy import Column, Integer, ForeignKey, Numeric, String
from database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    booking_id = Column(
        Integer,
        ForeignKey("bookings.id"),
        nullable=False
    )

    amount = Column(Numeric(10, 2), nullable=False)

    status = Column(
        String,
        nullable=False,
        default="PENDING"
    )
