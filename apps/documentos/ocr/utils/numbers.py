# apps/documentos/ocr/utils/numbers.py
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re

def clean_and_parse_amount(text: str) -> Decimal | None:
    """Converts an amount string to a Decimal object, removing symbols and dots."""
    if not text:
        return None
    
    # Removes everything that is not a digit
    cleaned_text = re.sub(r'[^\d]', '', text)
    if not cleaned_text:
        return None
        
    try:
        amount = Decimal(cleaned_text)
        # Only return the amount if it's greater than zero
        if amount > 0:
            return amount.quantize(Decimal("0"), rounding=ROUND_HALF_UP)
    except InvalidOperation:
        return None
    return None

def extract_iva_rate(text: str) -> Decimal | None:
    """Extracts an IVA rate (e.g., '19%') and returns it as a Decimal (19.00)."""
    match = re.search(r'\(?\s*(\d{1,2}(?:[\.,]\d+)?)\s*%\s*\)?', text, re.I)
    if match:
        rate_str = match.group(1).replace(",", ".")
        try:
            rate = Decimal(rate_str)
            return rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except InvalidOperation:
            return None
    return None