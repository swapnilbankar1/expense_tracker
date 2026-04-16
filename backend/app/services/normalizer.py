import re

def normalize_merchant(text: str) -> str:
    text = text.upper()
    text = re.sub(r"[^A-Z ]", "", text)
    text = re.sub(r"\s+", " ", text)

    stopwords = ["PAID TO", "PAYMENT", "CONFIRM"]
    for s in stopwords:
        text = text.replace(s, "")

    return text.strip()
