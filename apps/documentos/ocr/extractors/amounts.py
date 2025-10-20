# apps/documentos/ocr/extractors/amounts.py
import re
from decimal import Decimal
from ..utils import patterns
from ..utils.numbers import clean_and_parse_amount, extract_iva_rate

def extract_amounts(text: str) -> dict:
    """
    Extrae todos los montos de forma robusta, ideal para formatos de tabla o lista.
    """
    results = {
        'monto_neto': None, 'monto_exento': None, 'iva': None,
        'total': None, 'iva_tasa': None
    }
    
    # Dividir el texto en la sección de items y la sección de totales
    # para evitar confundir los montos de los productos con los finales.
    summary_text = text
    if "TOTAL" in text.upper():
        summary_text = text.upper().split("TOTAL")[0]
        # Nos quedamos con las últimas ~10 líneas para buscar los totales
        summary_text = "\n".join(summary_text.split('\n')[-10:]) + "\nTOTAL" + text.upper().split("TOTAL")[1]
    
    lines = summary_text.split('\n')
    
    # 1. Encontrar todas las etiquetas y todos los montos por separado
    found_labels = []
    found_amounts = []

    for line in lines:
        # Buscar etiquetas
        if patterns.ANCHOR_NETO.search(line): found_labels.append('neto')
        if patterns.ANCHOR_IVA.search(line) or '%' in line: found_labels.append('iva')
        if patterns.ANCHOR_TOTAL.search(line): found_labels.append('total')
        
        # Buscar montos
        for match in patterns.AMOUNT.finditer(line):
            amount = clean_and_parse_amount(match.group(0))
            if amount:
                found_amounts.append(amount)

    # 2. Asignar montos a etiquetas según su orden
    # Se asume que los montos aparecen en el mismo orden que las etiquetas (Neto, IVA, Total)
    
    # El total suele ser el más grande
    if found_amounts:
        results['total'] = max(found_amounts)
        found_amounts.remove(results['total'])

    # El neto suele ser el siguiente más grande
    if 'neto' in found_labels and found_amounts:
        results['monto_neto'] = max(found_amounts)
        found_amounts.remove(results['monto_neto'])
    
    # Lo que queda es el IVA
    if 'iva' in found_labels and found_amounts:
        results['iva'] = found_amounts[0]
        
    # Re-validación por si la heurística falló
    if results['monto_neto'] and results['iva'] and results['total']:
        if not (results['monto_neto'] + results['iva'] == results['total']):
             # Si la suma no cuadra, confiamos en la extracción individual
             pass # La reconciliación lo intentará arreglar

    # Extraer la tasa de IVA
    results['iva_tasa'] = extract_iva_rate(text)

    return results