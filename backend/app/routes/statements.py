from fastapi import APIRouter, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import shutil
import os

from app.core.database import SessionLocal
from app.services.pdf_reader import read_pdf_transactions
from app.services.normalizer import normalize_merchant
from app.services.categorizer import categorize
from app.services.monthly_expense_service import sync_monthly_expenses
from app.models.transaction import Transaction

router = APIRouter(prefix="/statements", tags=["Statements"])

UPLOAD_DIR = "data/statements"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
def upload_statement(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    transactions = read_pdf_transactions(file_path)
    
    print(f"Extracted {len(transactions)} transactions from PDF")
    if transactions:
        print(f"Sample transaction: {transactions[0]}")

    db: Session = SessionLocal()
    inserted = 0
    duplicates = 0

    for t in transactions:
        try:
            merchant_clean = normalize_merchant(t["description"])
            category = categorize({
                "merchant_clean": merchant_clean,
                "amount": t["amount"]
            })
            
            transaction_date = datetime.strptime(t["date"], "%b %d, %Y").date()
            transaction_amount = float(str(t["amount"]).replace("₹", "").replace(",", ""))
            
            # Check for duplicate transaction
            existing = db.query(Transaction).filter(
                Transaction.date == transaction_date,
                Transaction.merchant_raw == t["description"],
                Transaction.amount == transaction_amount
            ).first()
            
            if existing:
                print(f"Duplicate found: {transaction_date} | {t['description']} | {transaction_amount}")
                duplicates += 1
                continue

            txn = Transaction(
                date=transaction_date,
                merchant_raw=t["description"],
                merchant_clean=merchant_clean,
                amount=transaction_amount,
                category=category,
                transaction_type=t.get("type", "DEBIT"),
                source="phonepe"
            )

            db.add(txn)
            inserted += 1
        except Exception as e:
            print(f"Error processing transaction: {e}, data: {t}")
            continue

    db.commit()
    
    # Sync monthly expenses after inserting transactions
    sync_monthly_expenses(db)
    
    db.close()

    return {
        "message": "Statement processed",
        "transactions_inserted": inserted,
        "duplicates_skipped": duplicates
    }
