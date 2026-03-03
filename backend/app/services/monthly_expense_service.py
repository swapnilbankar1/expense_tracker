from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.transaction import Transaction
from app.models.monthly_expense import MonthlyExpense
from datetime import date
from calendar import month_name
from typing import List, Dict


def calculate_monthly_expenses(db: Session, year: int = None, month: int = None) -> List[Dict]:
    """
    Calculate month-wise expenses from transactions
    """
    query = db.query(
        func.extract('year', Transaction.date).label('year'),
        func.extract('month', Transaction.date).label('month'),
        Transaction.category,
        Transaction.source,
        func.sum(Transaction.amount).label('total_amount'),
        func.count(Transaction.id).label('transaction_count')
    )

    if year:
        query = query.filter(func.extract('year', Transaction.date) == year)
    if month:
        query = query.filter(func.extract('month', Transaction.date) == month)

    query = query.group_by(
        func.extract('year', Transaction.date),
        func.extract('month', Transaction.date),
        Transaction.category,
        Transaction.source
    ).order_by(
        func.extract('year', Transaction.date).desc(),
        func.extract('month', Transaction.date).desc()
    )

    results = query.all()

    return [
        {
            "year": int(row.year),
            "month": int(row.month),
            "category": row.category,
            "source": row.source,
            "total_amount": float(row.total_amount),
            "transaction_count": row.transaction_count
        }
        for row in results
    ]


def sync_monthly_expenses(db: Session):
    """
    Sync monthly expense summary table from transactions
    """
    # Clear existing monthly expenses
    db.query(MonthlyExpense).delete()

    # Recalculate from transactions
    monthly_data = calculate_monthly_expenses(db)

    for data in monthly_data:
        monthly_expense = MonthlyExpense(
            year=data["year"],
            month=data["month"],
            category=data["category"],
            source=data["source"],
            total_amount=data["total_amount"],
            transaction_count=data["transaction_count"]
        )
        db.add(monthly_expense)

    db.commit()


def get_monthly_summary(db: Session, year: int = None, month: int = None) -> List[Dict]:
    """
    Get month-wise expense summary grouped by year-month
    """
    monthly_data = calculate_monthly_expenses(db, year, month)

    # Group by year-month
    summary_dict = {}
    for data in monthly_data:
        key = (data["year"], data["month"])

        if key not in summary_dict:
            summary_dict[key] = {
                "year": data["year"],
                "month": data["month"],
                "month_name": month_name[data["month"]],
                "total_amount": 0,
                "transaction_count": 0,
                "categories": []
            }

        summary_dict[key]["total_amount"] += data["total_amount"]
        summary_dict[key]["transaction_count"] += data["transaction_count"]
        summary_dict[key]["categories"].append({
            "category": data["category"],
            "source": data["source"],
            "amount": data["total_amount"],
            "count": data["transaction_count"]
        })

    return list(summary_dict.values())
