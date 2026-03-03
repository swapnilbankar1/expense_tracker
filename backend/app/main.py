from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.services.pdf_reader import read_pdf_transactions
from app.services.normalizer import normalize_merchant
from app.services.categorizer import categorize
from app.core.database import SessionLocal
from app.models.transaction import Transaction
import os
from app.core.database import engine, Base

from app.routes import statements, categorize, transactions, monthly_expenses

app = FastAPI(title="Expense Tracker API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",      # Angular dev / Docker frontend
        "http://127.0.0.1:4200",      # Angular dev (127.0.0.1)
        "http://localhost:80",         # nginx in Docker
        "http://localhost",            # nginx in Docker (no port)
        "http://localhost:51935",      # Flutter web
        "http://127.0.0.1:51935",      # Flutter web
        "http://localhost:*",          # Any localhost port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(statements.router)
app.include_router(categorize.router)
app.include_router(transactions.router)
app.include_router(monthly_expenses.router)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"status": "ok", "service": "expense-tracker"}


# @app.on_event("startup")
# def process_statements():
#     folder = "data/statements"
#     db = SessionLocal()

#     for file in os.listdir(folder):
#         if not file.endswith(".pdf"):
#             continue

#         txns = read_pdf_transactions(os.path.join(folder, file))

#         for t in txns:
#             merchant = normalize_merchant(t["description"])
#             category = categorize({
#                 "merchant_clean": merchant,
#                 "amount": t["amount"]
#             })

#             db.add(Transaction(
#                 date=t["date"],
#                 merchant_raw=t["description"],
#                 merchant_clean=merchant,
#                 amount=float(str(t["amount"]).replace("₹", "").replace(",", "")),
#                 category=category,
#                 source="phonepe"
#             ))

#     db.commit()
