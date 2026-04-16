from sqlalchemy import Column, Integer, String, Float, Date
from app.core.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    transaction_id = Column(String, unique=True, index=True, nullable=True)
    date = Column(Date)
    merchant_raw = Column(String)
    merchant_clean = Column(String)
    amount = Column(Float)
    category = Column(String)
    transaction_type = Column(String)  # DEBIT / CREDIT
    source = Column(String)  # phonepe / credit card
    utr_no = Column(String, nullable=True)  # Bank UTR reference number
