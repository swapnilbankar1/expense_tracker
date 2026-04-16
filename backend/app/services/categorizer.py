from app.utils.rules import rule_based_category

# Keywords that indicate wallet top-ups or self-transfers (checked against raw description)
_TRANSFER_KEYWORDS = [
    "TOP-UP", "TOPUP", "ADD MONEY", "UPI LITE", "WALLET", "CASHBACK", "REFUND", "LOAD MONEY"
]


def categorize(txn: dict) -> str:
    merchant_clean = txn.get("merchant_clean", "")

    # Check rule-based category first (covers expanded RULES dict)
    rule = rule_based_category(merchant_clean)
    if rule:
        return rule

    # Fallback keyword check on merchant_clean for transfer/wallet operations
    merchant_upper = merchant_clean.upper()
    for kw in _TRANSFER_KEYWORDS:
        if kw in merchant_upper:
            return "Transfer"

    return "Other"
