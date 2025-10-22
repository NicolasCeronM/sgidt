# apps/documentos/ocr/extractors/amounts.py
import re
from decimal import Decimal
from ..utils import patterns
from ..utils.numbers import clean_and_parse_amount, extract_iva_rate

def extract_amounts(text: str) -> dict:
    """
    Extrae los montos de forma contextual, funcionando para múltiples diseños de factura.
    Utiliza una heurística basada en la magnitud de los montos.
    """
    results = {
        'monto_neto': None, 'monto_exento': None, 'iva': None,
        'total': None, 'iva_tasa': None
    }

    # 1. Aislar la sección de totales del documento y buscar todos los montos.
    summary_lines = text.split('\n')[-20:]
    summary_text = '\n'.join(summary_lines)
    
    all_amounts = [
        amount for match in patterns.AMOUNT.finditer(summary_text)
        if (amount := clean_and_parse_amount(match.group(0)))
    ]
    
    # Ordenar montos únicos de mayor a menor.
    unique_amounts = sorted(list(set(all_amounts)), reverse=True)
    
    if not unique_amounts:
        return results

    # 2. Buscar la presencia de etiquetas para guiar la asignación.
    has_neto_label = bool(patterns.ANCHOR_NETO.search(summary_text))
    has_iva_label = bool(patterns.ANCHOR_IVA.search(summary_text))
    has_total_label = bool(patterns.ANCHOR_TOTAL.search(summary_text))

    # 3. Asignar montos por magnitud (Total > Neto > IVA).
    # Asignar Total (casi siempre el más grande).
    if has_total_label and unique_amounts:
        results['total'] = unique_amounts.pop(0)

    # Asignar Neto (el siguiente más grande).
    if has_neto_label and unique_amounts:
        results['monto_neto'] = unique_amounts.pop(0)
        
    # Asignar IVA (lo que queda).
    if has_iva_label and unique_amounts:
        results['iva'] = unique_amounts.pop(0)

    # 4. Extraer la tasa de IVA de cualquier parte del documento.
    results['iva_tasa'] = extract_iva_rate(text)

    # 5. Reconciliación final para asegurar consistencia (esta parte es clave).
    neto, iva, total = results.get('monto_neto'), results.get('iva'), results.get('total')
    
    # Si después de la asignación, la suma no cuadra, podemos intentar corregirla.
    if neto and iva and total and abs((neto + iva) - total) > 2: # Tolerancia de 2
         # La heurística pudo fallar. Si tenemos 3 montos, los reasignamos forzando la suma.
         amounts = sorted([neto, iva, total], reverse=True)
         if len(amounts) == 3 and abs((amounts[1] + amounts[2]) - amounts[0]) <= 2:
              results['total'] = amounts[0]
              results['monto_neto'] = amounts[1]
              results['iva'] = amounts[2]
    
    # Calcular valores faltantes si es posible
    elif neto and iva and not total:
        results['total'] = neto + iva
    elif neto and total and not iva:
        if total > neto:
            results['iva'] = total - neto
    elif total and iva and not neto:
        if total > iva:
            results['monto_neto'] = total - iva
            
    return results