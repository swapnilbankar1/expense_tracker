import pdfplumber
import re
from datetime import datetime

def parse_phonepe_format(line: str) -> dict | None:
    """Parse PhonePe statement format: Oct 28, 2025  Merchant Name  DEBIT  ₹1,234.56"""
    pattern = r'^([A-Za-z]{3}\s+\d{1,2},\s+\d{4})\s+(.+?)\s+(DEBIT|CREDIT)\s+₹([\d,\.]+)$'
    match = re.match(pattern, line)
    
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
            "type": txn_type
        }
    return None

def parse_credit_card_format(line: str) -> dict | None:
    """Parse Credit Card statement formats:
    - DD/MM/YYYY  Merchant Name  1,234.56
    - DD-MM-YYYY  Merchant Name  1,234.56
    - DD MMM YYYY  Merchant Name  1,234.56
    """
    # Format 1: DD/MM/YYYY or DD-MM-YYYY
    pattern1 = r'^(\d{1,2}[/-]\d{1,2}[/-]\d{4})\s+(.+?)\s+(?:₹)?([\d,\.]+)$'
    match1 = re.match(pattern1, line)
    if match1:
        date_str = match1.group(1)
        description = match1.group(2).strip()
        amount = match1.group(3)
        
        # Convert date format
        try:
            if '/' in date_str:
                date_obj = datetime.strptime(date_str, "%d/%m/%Y")
            else:
                date_obj = datetime.strptime(date_str, "%d-%m-%Y")
            date_str = date_obj.strftime("%b %d, %Y")
        except:
            return None
        
        return {
            "date": date_str,
            "description": description,
            "amount": amount,
            "type": "DEBIT"  # Credit card transactions are typically debits
        }
    
    # Format 2: DD MMM YYYY
    pattern2 = r'^(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})\s+(.+?)\s+(?:₹)?([\d,\.]+)$'
    match2 = re.match(pattern2, line)
    if match2:
        date_str = match2.group(1)
        description = match2.group(2).strip()
        amount = match2.group(3)
        
        # Convert date format
        try:
            date_obj = datetime.strptime(date_str, "%d %b %Y")
            date_str = date_obj.strftime("%b %d, %Y")
        except:
            return None
        
        return {
            "date": date_str,
            "description": description,
            "amount": amount,
            "type": "DEBIT"
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
                lines = text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
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
