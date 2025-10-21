# apps/documentos/ocr/extractors/amounts.py
import re
from decimal import Decimal
from ..utils import patterns
from ..utils.numbers import clean_and_parse_amount, extract_iva_rate

def extract_amounts(text: str) -> dict:
    """
    Extrae los montos de forma contextual, funcionando para múltiples diseños de factura.
    """
    results = {
        'monto_neto': None, 'monto_exento': None, 'iva': None,
        'total': None, 'iva_tasa': None
    }
    
    # 1. Aislar la sección de totales del documento (generalmente las últimas 15-20 líneas)
    summary_lines = text.split('\n')[-20:]

    # 2. Encontrar todas las etiquetas y montos en esa sección
    found_labels = {}
    found_amounts = {}
    for i, line in enumerate(summary_lines):
        # Buscar etiquetas y guardar su número de línea
        if patterns.ANCHOR_NETO.search(line) and 'neto' not in found_labels: found_labels['neto'] = i
        if patterns.ANCHOR_IVA.search(line) and 'iva' not in found_labels: found_labels['iva'] = i
        if patterns.ANCHOR_TOTAL.search(line) and 'total' not in found_labels: found_labels['total'] = i
        
        # Buscar montos y guardar su valor y número de línea
        for match in patterns.AMOUNT.finditer(line):
            amount = clean_and_parse_amount(match.group(0))
            if amount:
                if i not in found_amounts:
                    found_amounts[i] = []
                found_amounts[i].append(amount)

    # 3. Asignar montos a etiquetas de forma inteligente
    for label, line_idx in found_labels.items():
        value = None
        # Prioridad 1: Buscar monto en la misma línea que la etiqueta
        if line_idx in found_amounts:
            value = found_amounts[line_idx][0]
        # Prioridad 2: Si no, buscar en las líneas cercanas (hacia abajo), saltando las vacías
        else:
            closest_line = min(found_amounts.keys(), key=lambda k: abs(k - line_idx) if k > line_idx else 999, default=None)
            if closest_line:
                value = found_amounts[closest_line][0]
        
        if label == 'neto': results['monto_neto'] = value
        elif label == 'iva': results['iva'] = value
        elif label == 'total': results['total'] = value

    # 4. Extraer la tasa de IVA de cualquier parte del documento
    results['iva_tasa'] = extract_iva_rate(text)

    # 5. Reconciliación final para asegurar consistencia
    neto, iva, total = results.get('monto_neto'), results.get('iva'), results.get('total')
    if neto and iva and not total:
        results['total'] = neto + iva
    elif neto and total and not iva:
        if total > neto:
            results['iva'] = total - neto
    elif total and iva and not neto:
        if total > iva:
            results['monto_neto'] = total - iva
            
    return results