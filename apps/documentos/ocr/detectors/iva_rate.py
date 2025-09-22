# -*- coding: utf-8 -*-
import re
from ..utils.numbers import safe_rate

def detect_iva_rate(text: str) -> float | None:
    r = safe_rate(text)
    if r: return r
    if re.search(r"\bIVA\b", text, re.I): return 0.19
    return None
