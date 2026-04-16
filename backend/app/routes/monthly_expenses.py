from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import Optional, List
import shutil
import os
import traceback

from app.core.database import SessionLocal
from app.services.pdf_reader import read_pdf_transactions
from app.services.normalizer import normalize_merchant
from app.services.categorizer import categorize
from app.services.monthly_expense_service import get_monthly_summary, sync_monthly_expenses
from app.models.transaction import Transaction
from app.schemas.monthly_expense import (
    MonthlyExpenseSummary,
    PDFUploadResponse
)

router = APIRouter(prefix="/monthly-expenses", tags=["Monthly Expenses"])

UPLOAD_DIR = "data/statements"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload-pdf", response_model=PDFUploadResponse)
def upload_pdf_and_generate_monthly_expenses(file: UploadFile = File(...)):
    """
    Upload a PDF statement, extract transactions, and return month-wise expense summary
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    # Save uploaded PDF
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Read transactions from PDF
    transactions = read_pdf_transactions(file_path)

    db: Session = SessionLocal()
    inserted = 0
    duplicates = 0
    failed = 0

    # Process and save transactions
    for t in transactions:
        try:
            merchant_clean = normalize_merchant(t["description"])
            category = categorize({
                "merchant_clean": merchant_clean,
                "amount": t["amount"]
            })
            
            transaction_date = datetime.strptime(t["date"], "%b %d, %Y").date()
            transaction_amount = float(str(t["amount"]).replace("₹", "").replace(",", ""))
            external_txn_id = t.get("transaction_id") or t.get("id")
            
            # Check for duplicate transaction
            if external_txn_id:
                existing = db.query(Transaction).filter(
                    Transaction.transaction_id == external_txn_id
                ).first()
            else:
                existing = db.query(Transaction).filter(
                    Transaction.date == transaction_date,
                    Transaction.merchant_raw == t["description"],
                    func.abs(Transaction.amount - transaction_amount) < 0.01,
                    Transaction.transaction_type == t.get("type", "DEBIT"),
                    Transaction.source == t.get("source", "phonepe")
                ).first()

            if existing:
                duplicates += 1
                continue

            txn = Transaction(
                transaction_id=external_txn_id,
                date=transaction_date,
                merchant_raw=t["description"],
                merchant_clean=merchant_clean,
                amount=transaction_amount,
                category=category,
                transaction_type=t.get("type", "DEBIT"),
                source=t.get("source", "phonepe"),
                utr_no=t.get("utr_no")
            )

            db.add(txn)
            inserted += 1
        except Exception as e:
            print(f"Error processing transaction: {e}")
            traceback.print_exc()
            failed += 1
            continue

    try:
        db.commit()
    except Exception as e:
        print(f"Error committing transactions: {e}")
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save transactions to database")

    # Generate monthly expense summary
    sync_monthly_expenses(db)
    monthly_summary = get_monthly_summary(db)

    db.close()

    return PDFUploadResponse(
        message="PDF processed successfully",
        transactions_inserted=inserted,
        duplicates_skipped=duplicates,
        failed_transactions=failed,
        monthly_summary=monthly_summary
    )


@router.get("/summary", response_model=List[MonthlyExpenseSummary])
def get_monthly_expense_summary(
    year: Optional[int] = Query(None, description="Filter by year"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Filter by month (1-12)")
):
    """
    Get month-wise expense summary
    """
    db: Session = SessionLocal()

    try:
        summary = get_monthly_summary(db, year=year, month=month)
        return summary
    finally:
        db.close()


@router.get("/categories")
def get_expenses_by_category(
    year: Optional[int] = Query(None, description="Filter by year"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Filter by month (1-12)")
):
    """
    Get expenses grouped by category for a specific month
    """
    db: Session = SessionLocal()

    try:
        monthly_data = get_monthly_summary(db, year=year, month=month)

        # Aggregate all categories across months
        category_totals = {}
        for month_data in monthly_data:
            for cat in month_data["categories"]:
                category = cat["category"]
                if category not in category_totals:
                    category_totals[category] = {
                        "category": category,
                        "total_amount": 0,
                        "total_debit": 0,
                        "total_credit": 0,
                        "transaction_count": 0,
                        "debit_count": 0,
                        "credit_count": 0
                    }

                category_totals[category]["total_amount"] += cat["amount"]
                category_totals[category]["total_debit"] += cat.get("debit_amount", 0)
                category_totals[category]["total_credit"] += cat.get("credit_amount", 0)
                category_totals[category]["transaction_count"] += cat["count"]
                category_totals[category]["debit_count"] += cat.get("debit_count", 0)
                category_totals[category]["credit_count"] += cat.get("credit_count", 0)

        return {
            "year": year,
            "month": month,
            "categories": list(category_totals.values())
        }
    finally:
        db.close()


@router.post("/sync")
def sync_monthly_expense_table():
    """
    Manually trigger sync of monthly expenses from transactions
    """
    db: Session = SessionLocal()

    try:
        sync_monthly_expenses(db)
        return {"message": "Monthly expenses synced successfully"}
    finally:
        db.close()
