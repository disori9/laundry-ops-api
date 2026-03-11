from pydantic import BaseModel


class CustomerCreate(BaseModel):
    cust_name: str
    number: str