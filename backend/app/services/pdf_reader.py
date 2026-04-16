import pdfplumber
import re
from datetime import datetime

PHONEPE_ROW_PATTERN = re.compile(
    r'^([A-Za-z]{3}\s+\d{1,2},\s+\d{4})\s+(.+?)\s+(DEBIT|CREDIT)\s+₹([\d,]+(?:\.\d+)?)$'
)
PHONEPE_DATE_PREFIX = re.compile(r'^[A-Za-z]{3}\s+\d{1,2},\s+\d{4}\b')
PHONEPE_TIME_PREFIX = re.compile(r'^\d{1,2}:\d{2}\s*(?:am|pm)\s+', re.IGNORECASE)
TRANSACTION_ID_LINE = re.compile(r"^Transaction ID\s+([A-Z0-9]+)$", re.IGNORECASE)
TRANSACTION_ID_ONLY = re.compile(r"^[A-Z0-9]{12,}$")
PHONEPE_UTR_LINE = re.compile(r"^UTR No\.\s*(.+)$", re.IGNORECASE)
PHONEPE_STANDALONE_TIME = re.compile(r'^\d{1,2}:\d{2}\s*(?:am|pm)$', re.IGNORECASE)


def _to_display_date(date_str: str) -> str | None:
    for date_format in ("%d/%m/%Y", "%d-%m-%Y", "%d %b %Y"):
        try:
            return datetime.strptime(date_str, date_format).strftime("%b %d, %Y")
        except ValueError:
            continue
    return None


def parse_phonepe_format(line: str) -> dict | None:
    """Parse PhonePe statement format: Oct 28, 2025  Merchant Name  DEBIT  ₹1,234.56"""
    match = PHONEPE_ROW_PATTERN.match(line)
    
    if match:
        date_str = match.group(1)
        description = match.group(2)
        txn_type = match.group(3)
        amount = match.group(4)
        
        # Clean up description
        description = description.replace('Paid to ', '').replace('Received from ', '').strip()
        
        return {
            "date": date_str,
            "description": description,
            "amount": amount,
            "type": txn_type,
            "source": "phonepe",
            "id": None,
            "transaction_id": None
        }
    return None


def _normalize_phonepe_description(description: str) -> str:
    description = re.sub(r"\s+", " ", description).strip()
    # Strip leading time token (e.g. "11:45 am ") that pdfplumber merges into description
    description = re.sub(r'^\d{1,2}:\d{2}\s*(?:am|pm)\s+', '', description, flags=re.IGNORECASE)
    description = re.sub(r"^Paid to\s+", "", description, flags=re.IGNORECASE)
    description = re.sub(r"^Received from\s+", "", description, flags=re.IGNORECASE)
    description = re.sub(
        r"\s+Transaction ID(?:\s+[A-Z0-9]+)?$",
        "",
        description,
        flags=re.IGNORECASE
    )
    return description.strip()


def _extract_phonepe_transactions_from_lines(lines: list[str]) -> list[dict]:
    transactions: list[dict] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        match = PHONEPE_ROW_PATTERN.match(line)
        if not match:
            i += 1
            continue

        date_str = match.group(1)
        description = match.group(2).strip()
        txn_type = match.group(3).strip()
        amount = match.group(4).strip()
        transaction_id = None
        utr_no = None

        j = i + 1
        detail_chunks: list[str] = []

        while j < len(lines):
            next_line = lines[j]
            if PHONEPE_DATE_PREFIX.match(next_line) or next_line.startswith("Page "):
                break
            txid_match = TRANSACTION_ID_LINE.match(next_line)
            if txid_match:
                transaction_id = txid_match.group(1)
                j += 1
                continue
            utr_match = PHONEPE_UTR_LINE.match(next_line)
            if utr_match:
                utr_no = utr_match.group(1).strip()
                j += 1
                continue
            if next_line.startswith("Paid by ") or next_line.startswith("Credited to "):
                j += 1
                continue
            if re.match(r'^Date\s+Transaction', next_line):
                j += 1
                continue
            if next_line.startswith("This is a system generated statement"):
                j += 1
                continue

            # Time line may carry wrapped merchant details after the time token.
            candidate = PHONEPE_TIME_PREFIX.sub("", next_line).strip()
            txid_match = TRANSACTION_ID_LINE.match(candidate)
            if txid_match:
                transaction_id = txid_match.group(1)
                j += 1
                continue
            # Some statements split Transaction ID across two lines:
            # "01:52 pm Transaction ID" + next line "<ID>"
            if candidate == "Transaction ID":
                if j + 1 < len(lines):
                    id_candidate = lines[j + 1].strip()
                    if TRANSACTION_ID_ONLY.fullmatch(id_candidate):
                        transaction_id = id_candidate
                        j += 2
                        continue
                j += 1
                continue
            if TRANSACTION_ID_ONLY.fullmatch(candidate):
                j += 1
                continue
            # Skip standalone time-only lines (e.g. "11:45 am" with no trailing merchant text)
            if PHONEPE_STANDALONE_TIME.fullmatch(candidate):
                j += 1
                continue
            if candidate:
                detail_chunks.append(candidate)
            j += 1

        if detail_chunks:
            description = f"{description} {' '.join(detail_chunks)}".strip()

        description = _normalize_phonepe_description(description)
        if not description:
            description = "Unknown"

        transactions.append({
            "date": date_str,
            "description": description,
            "amount": amount,
            "type": txn_type,
            "source": "phonepe",
            "id": transaction_id,
            "transaction_id": transaction_id,
            "utr_no": utr_no
        })
        i = j

    return transactions


def parse_credit_card_format(line: str) -> dict | None:
    """Parse Credit Card statement formats:
    - DD/MM/YYYY  Merchant Name  1,234.56
    - DD-MM-YYYY  Merchant Name  1,234.56
    - DD MMM YYYY  Merchant Name  1,234.56
    """
    # Format 1: DD/MM/YYYY or DD-MM-YYYY
    pattern1 = r'^(\d{1,2}[/-]\d{1,2}[/-]\d{4})\s+(.+?)\s+(?:₹)?([\d,\.]+)\s*(Dr|Cr|DR|CR)?$'
    match1 = re.match(pattern1, line)
    if match1:
        date_str = match1.group(1)
        description = match1.group(2).strip()
        amount = match1.group(3)
        suffix = match1.group(4)
        
        parsed_date = _to_display_date(date_str)
        if not parsed_date:
            return None
        date_str = parsed_date
        
        txn_type = "CREDIT" if suffix and suffix.upper() == "CR" else "DEBIT"
        
        return {
            "date": date_str,
            "description": description,
            "amount": amount,
            "type": txn_type,
            "source": "credit_card",
            "id": None,
            "transaction_id": None
        }
    
    # Format 2: DD MMM YYYY
    pattern2 = r'^(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})\s+(.+?)\s+(?:₹)?([\d,\.]+)\s*(Dr|Cr|DR|CR)?$'
    match2 = re.match(pattern2, line)
    if match2:
        date_str = match2.group(1)
        description = match2.group(2).strip()
        amount = match2.group(3)
        suffix = match2.group(4)
        
        parsed_date = _to_display_date(date_str)
        if not parsed_date:
            return None
        date_str = parsed_date
        
        txn_type = "CREDIT" if suffix and suffix.upper() == "CR" else "DEBIT"
        
        return {
            "date": date_str,
            "description": description,
            "amount": amount,
            "type": txn_type,
            "source": "credit_card",
            "id": None,
            "transaction_id": None
        }

    # Format 3: HDFC style OCR line
    # Example: 05/01/2026| 18:53 SHREE SKY VENTURESPUNE + 28 C 1,119.00 l
    pattern3 = r'^(\d{1,2}[/-]\d{1,2}[/-]\d{4})\|\s*\d{1,2}:\d{2}\s+(.+?)\s+(?:\+\s*\d+\s+)?[CD]\s*(?:₹)?([\d,]+(?:\.\d+)?)\b'
    match3 = re.match(pattern3, line)
    if match3:
        date_str = match3.group(1)
        description = match3.group(2).strip()
        amount = match3.group(3)

        parsed_date = _to_display_date(date_str)
        if not parsed_date:
            return None

        return {
            "date": parsed_date,
            "description": description,
            "amount": amount,
            # Card statement purchases/debits often OCR currency marker as C.
            "type": "DEBIT",
            "source": "credit_card",
            "id": None,
            "transaction_id": None
        }
    
    return None

def read_pdf_transactions(pdf_path: str) -> list[dict]:
    transactions = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"PDF has {len(pdf.pages)} pages")
            
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                
                if not text:
                    continue
                
                # Split by lines
                lines = [line.strip() for line in text.split('\n') if line.strip()]

                # PhonePe statements often wrap merchant details in the next line.
                page_phonepe_transactions = _extract_phonepe_transactions_from_lines(lines)
                if page_phonepe_transactions:
                    for result in page_phonepe_transactions:
                        transactions.append(result)
                        print(f"Extracted: {result['date']} | {result['description']} | {result['type']} | {result['amount']}")
                    continue
                
                for line in lines:
                    # Try PhonePe format first
                    result = parse_phonepe_format(line)
                    
                    # If not PhonePe, try credit card formats
                    if not result:
                        result = parse_credit_card_format(line)
                    
                    if result:
                        transactions.append(result)
                        print(f"Extracted: {result['date']} | {result['description']} | {result['type']} | {result['amount']}")
                
    except Exception as e:
        print(f"Error reading PDF: {e}")
        import traceback
        traceback.print_exc()
        
    print(f"Total transactions extracted: {len(transactions)}")
    return transactions
