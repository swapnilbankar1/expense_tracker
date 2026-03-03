from sqlalchemy import Column, Integer, String, Float, Date
from app.core.database import Base


class MonthlyExpense(Base):
    __tablename__ = "monthly_expenses"

    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    category = Column(String, nullable=True)
    total_amount = Column(Float, nullable=False)
    transaction_count = Column(Integer, default=0)
    source = Column(String)  # phonepe / credit card
