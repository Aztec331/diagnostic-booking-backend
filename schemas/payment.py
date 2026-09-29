from pydantic import BaseModel, Field


class PaymentCreate(BaseModel):
    booking_id: int


class PaymentWebhook(BaseModel):
    event_id: str = Field(min_length=1)
    payment_id: int
    event_type: str