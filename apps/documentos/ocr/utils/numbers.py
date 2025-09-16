# -*- coding: utf-8 -*-
from decimal import Decimal, ROUND_HALF_UP

def normalize_amount(s: str) -> Decimal | None:
    if not s: return None
    s = s.replace(".", "").replace(",", ".").replace(" ", "")
    try: return Decimal(s)
    except Exception: return None

def round0(x: Decimal) -> Decimal:
    return x.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
