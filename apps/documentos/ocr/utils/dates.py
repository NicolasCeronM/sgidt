# -*- coding: utf-8 -*-
import re
from datetime import datetime

MESES = {
    "enero":1, "febrero":2, "marzo":3, "abril":4, "mayo":5, "junio":6,
    "julio":7, "agosto":8, "septiembre":9, "setiembre":9, "octubre":10,
    "noviembre":11, "diciembre":12
}

# "01 de Septiembre del 2025" (permite uno o dos espacios y 'del'/'de')
RE_FECHA_TXT = re.compile(
    r"(\d{1,2})\s+de\s+([A-Za-záéíóúñÑ]+)\s+del?\s+(\d{4})",
    re.I
)

RE_FECHA_NUM = re.compile(r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})")

_WS = re.compile(r"\s+", re.UNICODE)

def normalize_spaces(t: str) -> str:
    """Colapsa espacios raros (NBSP, tabs, etc.) a ' ' y trim."""
    if not t: return ""
    return _WS.sub(" ", t).strip()

def parse_date_any(text: str):
    if not text: return None
    t = normalize_spaces(text)

    m = RE_FECHA_TXT.search(t)
    if m:
        d = int(m.group(1))
        mes = MESES.get(m.group(2).lower())
        a  = int(m.group(3))
        if mes:
            return datetime(a, mes, d).date()

    m = RE_FECHA_NUM.search(t)
    if m:
        d, mes, a = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if a < 100: a += 2000 if a < 50 else 1900
        return datetime(a, mes, d).date()

    return None
