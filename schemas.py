from pydantic import BaseModel
from typing import Literal


class CustomerCreate(BaseModel):
    cust_name: str
    number: str


class OrderCreate(BaseModel):
    customer_id: int
    weight_kg: float
    payment_status: Literal['PAID', 'UNPAID']
