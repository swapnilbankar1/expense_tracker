from pydantic import BaseModel
from datetime import date
from typing import Optional


class TransactionBase(BaseModel):
    transaction_id: Optional[str] = None
    date: date
    merchant_raw: str
    merchant_clean: str
    amount: float
    category: Optional[str] = None
    transaction_type: str = "DEBIT"
    source: str


class TransactionCreate(TransactionBase):
    pass


class TransactionResponse(TransactionBase):
    id: int

    class Config:
        from_attributes = True
