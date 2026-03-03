RULES = {
    "ZOMATO": "Food",
    "SWIGGY": "Food",
    "ARRIVA MEDICAL": "Medical",
    "PATEL CHEMIST": "Medical",
    "NETFLIX": "Entertainment",
    "ELECTRICITY": "Utilities",
    "AMAZON": "Shopping",
}

def rule_based_category(merchant: str):
    for key, category in RULES.items():
        if key in merchant:
            return category
    return None
