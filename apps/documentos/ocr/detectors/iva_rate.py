# -*- coding: utf-8 -*-
from decimal import Decimal
from ..patterns import IVA_RATE_RE

def guess_iva_rate(text: str) -> Decimal | None:
    m = IVA_RATE_RE.search((text or "").upper())
    if m:
        try: return Decimal(m.group(1))
        except Exception: return None
    return Decimal("19")
