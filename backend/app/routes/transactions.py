from fastapi import APIRouter, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import Optional

from app.core.database import SessionLocal
from app.models.transaction import Transaction

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("")
def get_transactions(
    category: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = Query(50, le=1000),
    offset: int = 0
):
    db: Session = SessionLocal()
    query = db.query(Transaction)

    if category:
        query = query.filter(Transaction.category == category)

    if start_date:
        query = query.filter(Transaction.date >= start_date)

    if end_date:
        query = query.filter(Transaction.date <= end_date)

    results = (
        query
        .order_by(Transaction.date.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    db.close()
    return results


@router.get("/by-merchant")
def get_transactions_by_merchant(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    merchant: Optional[str] = None,
    sort_by: str = Query("amount", regex="^(amount|count|merchant)$")
):
    """
    Get aggregated transactions grouped by merchant.
    Shows total amount and transaction count for each merchant.
    """
    db: Session = SessionLocal()
    
    query = db.query(
        Transaction.merchant_clean.label('merchant'),
        func.sum(Transaction.amount).label('total_amount'),
        func.count(Transaction.id).label('transaction_count')
    )
    
    # Apply filters
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    if merchant:
        query = query.filter(Transaction.merchant_clean.ilike(f'%{merchant}%'))
    
    # Group by merchant
    query = query.group_by(Transaction.merchant_clean)
    
    # Sort
    if sort_by == "amount":
        query = query.order_by(func.sum(Transaction.amount).desc())
    elif sort_by == "count":
        query = query.order_by(func.count(Transaction.id).desc())
    else:  # merchant
        query = query.order_by(Transaction.merchant_clean)
    
    results = query.all()
    
    db.close()
    
    return [
        {
            "merchant": row.merchant,
            "total_amount": float(row.total_amount) if row.total_amount else 0,
            "transaction_count": row.transaction_count,
            "average_amount": float(row.total_amount / row.transaction_count) if row.transaction_count else 0
        }
        for row in results
    ]
