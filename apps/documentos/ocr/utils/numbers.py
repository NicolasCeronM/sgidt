# apps/documentos/ocr/utils/numbers.py
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re

def clean_and_parse_amount(text: str) -> Decimal | None:
    """Convierte un texto de monto a un objeto Decimal, eliminando símbolos y puntos."""
    if not text:
        return None
    
    cleaned_text = re.sub(r'[^\d]', '', text)
    if not cleaned_text:
        return None
        
    try:
        amount = Decimal(cleaned_text)
        if amount > 0:
            return amount.quantize(Decimal("0"), rounding=ROUND_HALF_UP)
    except InvalidOperation:
        return None
    return None

def extract_iva_rate(text: str) -> Decimal | None:
    """
    Extrae una tasa de IVA (ej: '19%' o '(1 9%)') y la devuelve como Decimal (19.00).
    """
    # Regex MEJORADA: Tolera espacios opcionales entre los dígitos y el '%'
    match = re.search(r'\(?\s*(\d{1,2})\s*(\d?)\s*%\s*\)?', text, re.I)
    if match:
        # Une los dígitos si están separados por un espacio (ej: '1' y '9')
        rate_str = match.group(1) + (match.group(2) or '')
        try:
            rate = Decimal(rate_str)
            return rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except InvalidOperation:
            return None
    return None