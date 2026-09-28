from pydantic import BaseModel


class CentreCreate(BaseModel):
    name: str
    location: str

class CentreTestCreate(BaseModel):
    test_id: int
    price: float