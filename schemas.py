from pydantic import BaseModel
from typing import Literal, Optional


class CustomerCreate(BaseModel):
    cust_name: str
    number: str


class OrderCreate(BaseModel):
    customer_id: int
    weight_kg: float
    payment_status: Literal['PAID', 'UNPAID']
    comforter_count: int=0


class OrderItemCreate(BaseModel):
    order_id: int
    category_id: int
    initial_count: int


class LoadStatusUpdate(BaseModel):
    status: Literal['RECEIVED', 'WASHING', 'DRYING', 'FOLDING', 'BAGGED', 'COMPLETED']
    machine_no: Optional[int] = None


class ItemVerification(BaseModel):
    verified_count: int
    