from fastapi import APIRouter, HTTPException
from app.services.categorizer import categorize

router = APIRouter(prefix="/categorize", tags=["Categorization"])


@router.post("")
def categorize_transaction(payload: dict):
    merchant = payload.get("merchant")
    amount = payload.get("amount")

    if not merchant or amount is None:
        raise HTTPException(status_code=400, detail="merchant and amount required")

    category = categorize({
        "merchant_clean": merchant,
        "amount": amount
    })

    return {
        "merchant": merchant,
        "amount": amount,
        "category": category
    }
