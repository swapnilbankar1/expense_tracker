from app.core.database import engine, Base
from app.models.transaction import Transaction
from app.models.monthly_expense import MonthlyExpense

# Import all models so they are registered with Base
Base.metadata.create_all(bind=engine)
print("DB tables created")
