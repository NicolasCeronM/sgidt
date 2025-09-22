# -*- coding: utf-8 -*-
import re
from ..utils.text_norm import normalize_text

_RE_FACTURA = re.compile(r"\bFACTURA\b", re.I)
_RE_BOLETA  = re.compile(r"\bBOLETA\b", re.I)
_RE_NC      = re.compile(r"NOTA\s+DE\s+CR[EÉ]DITO", re.I)
_RE_EXENTA  = re.compile(r"\bEXENTA?\b", re.I)
_RE_IVA     = re.compile(r"\bI\.?V\.?A\.?\b|\bIVA\b", re.I)

def detect_tipo_dte(text: str):
    t = normalize_text(text or "")
    if not t: return "desconocido", "Documento Desconocido"

    if _RE_NC.search(t):
        return "nota_credito", "Nota de Crédito"
    if _RE_FACTURA.search(t):
        if _RE_EXENTA.search(t) and not _RE_IVA.search(t):
            return "factura_exenta", "Factura Electrónica Exenta"
        return "factura_afecta", "Factura Electrónica"
    if _RE_BOLETA.search(t):
        if _RE_EXENTA.search(t) and not _RE_IVA.search(t):
            return "boleta_exenta", "Boleta Electrónica Exenta"
        return "boleta_afecta", "Boleta Electrónica"

    return "desconocido", "Documento Desconocido"
