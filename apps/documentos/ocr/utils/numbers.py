# -*- coding: utf-8 -*-
from decimal import Decimal, ROUND_HALF_UP
import re

def to_int_money(s: str) -> int | None:
    if not s: return None
    s = s.strip().replace("$","").replace(" ","")
    s = s.replace(".", "").replace(",", ".")
    try:
        val = Decimal(s)
        return int(val.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except:
        return None

def safe_rate(iva_text: str) -> float | None:
    m = re.search(r"(\d{1,2})(?:[.,](\d))?\s*%", iva_text or "", re.I)
    if not m: return None
    ent = int(m.group(1)); dec = int(m.group(2)) if m.group(2) else 0
    return (ent + dec/10) / 100.0
