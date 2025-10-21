# apps/documentos/ocr/extractors/amounts.py
import re
from decimal import Decimal
from ..utils import patterns
from ..utils.numbers import clean_and_parse_amount, extract_iva_rate

def find_amount_on_line(line: str) -> Decimal | None:
    """Encuentra el primer monto válido en una sola línea."""
    match = patterns.AMOUNT.search(line)
    if match:
        return clean_and_parse_amount(match.group(0))
    return None

def extract_amounts(text: str) -> dict:
    """
    Extrae todos los montos con alta precisión, evitando la contaminación entre líneas.
    """
    results = {
        'monto_neto': None, 'monto_exento': None, 'iva': None,
        'total': None, 'iva_tasa': None
    }
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        # Para cada etiqueta, buscamos el monto prioritariamente en su propia línea.
        if patterns.ANCHOR_NETO.search(line) and results['monto_neto'] is None:
            results['monto_neto'] = find_amount_on_line(line)

        elif patterns.ANCHOR_IVA.search(line) and results['iva'] is None:
            results['iva'] = find_amount_on_line(line)
            if results['iva_tasa'] is None:
                results['iva_tasa'] = extract_iva_rate(line)

        elif patterns.ANCHOR_TOTAL.search(line) and results['total'] is None:
            results['total'] = find_amount_on_line(line)

    # Lógica de Reconciliación Simple: Si falta un valor, lo calculamos.
    neto, iva, total = results['monto_neto'], results['iva'], results['total']
    if neto and iva and not total:
        results['total'] = neto + iva
    elif neto and total and not iva:
        calculated_iva = total - neto
        if abs(calculated_iva - (neto * Decimal('0.19'))) < 2: # Verificación de consistencia
            results['iva'] = calculated_iva
    elif total and iva and not neto:
        results['monto_neto'] = total - iva
        
    return results