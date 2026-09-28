from datetime import datetime

from pydantic import BaseModel


class BookingCreate(BaseModel):
    centre_id: int
    test_id: int
    appointment_at: datetime