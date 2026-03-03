from pydantic import BaseModel
from typing import Optional, List


class MonthlyExpenseBase(BaseModel):
    year: int
    month: int
    category: Optional[str] = None
    total_amount: float
    transaction_count: int
    source: str


class MonthlyExpenseResponse(MonthlyExpenseBase):
    id: int

    class Config:
        from_attributes = True


class MonthlyExpenseSummary(BaseModel):
    year: int
    month: int
    month_name: str
    total_amount: float
    transaction_count: int
    categories: List[dict]  # List of {category, amount, count}


class MonthlyExpensesByCategory(BaseModel):
    category: str
    total_amount: float
    transaction_count: int


class PDFUploadResponse(BaseModel):
    message: str
    transactions_inserted: int
    duplicates_skipped: int
    monthly_summary: List[MonthlyExpenseSummary]
