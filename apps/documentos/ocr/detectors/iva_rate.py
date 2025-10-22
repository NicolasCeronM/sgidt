# -*- coding: utf-8 -*-
import re
from ..utils.numbers import clean_and_parse_amount

def detect_iva_rate(text: str) -> float | None:
    r = clean_and_parse_amount(text)
    if r: return r
    if re.search(r"\bIVA\b", text, re.I): return 0.19
    return None
