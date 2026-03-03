from app.core.llm import classify_transaction
from app.utils.rules import rule_based_category

CATEGORIES = [
    "Food", "Groceries", "Medical", "Utilities",
    "Travel", "Shopping", "Entertainment",
    "Investment", "Transfer", "Other"
]

def categorize(txn: dict) -> str:
    rule = rule_based_category(txn["merchant_clean"])
    if rule:
        return rule

    prompt = f"""
Classify this transaction into ONE category.

Merchant: {txn['merchant_clean']}
Amount: {txn['amount']}
Country: India

Categories: {", ".join(CATEGORIES)}

Respond ONLY with category name.
"""

    return classify_transaction(prompt)
