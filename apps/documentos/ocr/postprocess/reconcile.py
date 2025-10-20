# apps/documentos/ocr/postprocess/reconcile.py
from decimal import Decimal

DEFAULT_IVA_RATE = Decimal('19.00')

def reconcile_amounts(extracted_data: dict) -> dict:
    """
    Valida y reconcilia los montos extraídos.
    Infiere valores faltantes solo si es lógicamente posible.
    """
    neto = extracted_data.get('monto_neto')
    exento = extracted_data.get('monto_exento') or Decimal('0')
    iva = extracted_data.get('iva')
    total = extracted_data.get('total')
    iva_tasa = extracted_data.get('iva_tasa')

    # --- Lógica de Inferencia ---

    # Escenario 1: Falta el TOTAL, pero tenemos NETO e IVA.
    if total is None and neto is not None and iva is not None:
        total = neto + exento + iva
        
    # Escenario 2: Falta el IVA, pero tenemos NETO y TOTAL.
    elif iva is None and neto is not None and total is not None:
        calculated_iva = total - neto - exento
        expected_rate = iva_tasa or DEFAULT_IVA_RATE
        if neto > Decimal('0'):
            expected_iva = neto * (expected_rate / Decimal('100'))
            if abs(calculated_iva - expected_iva) < 2:
                iva = calculated_iva

    # Escenario 3: Falta el NETO, pero tenemos TOTAL e IVA.
    elif neto is None and total is not None and iva is not None:
        neto = total - iva - exento

    # --- Asignación Final ---
    return {
        'monto_neto': neto,
        'monto_exento': exento if exento > Decimal('0') else None,
        'iva': iva,
        'total': total,
        'iva_tasa': iva_tasa
    }