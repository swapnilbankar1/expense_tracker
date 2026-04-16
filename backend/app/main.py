from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base

from app.routes import categorize, transactions, monthly_expenses

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

app.include_router(categorize.router)
app.include_router(transactions.router)
app.include_router(monthly_expenses.router)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"status": "ok", "service": "expense-tracker"}
