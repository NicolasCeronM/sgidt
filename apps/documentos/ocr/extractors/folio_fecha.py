# -*- coding: utf-8 -*-
from datetime import datetime, date
from typing import Optional
from ..patterns import FOLIO_RE, FECHA_RE_NUM, FECHA_RE_TXT, MESES
from ..utils.text_norm import strip_accents

def extract_folio(text: str) -> str | None:
    m = FOLIO_RE.search(text or "")
    return m.group(1) if m else None

def _parse_date_numeric(s: str) -> Optional[date]:
    for fmt in ("%d-%m-%Y","%d/%m/%Y","%d.%m.%Y","%d-%m-%y","%d/%m/%y","%d.%m.%y","%Y-%m-%d","%Y/%m/%d","%Y.%m.%d"):
        try: return datetime.strptime(s, fmt).date()
        except Exception: continue
    return None

def _month_from_text(mtxt: str) -> Optional[int]:
    s = strip_accents(mtxt or "").lower().strip(". ")
    if s in MESES: return MESES[s]
    from difflib import get_close_matches
    cand = get_close_matches(s, MESES.keys(), n=1, cutoff=0.7)
    return MESES[cand[0]] if cand else None

def _parse_date_textual(m) -> Optional[date]:
    try:
        d = int(m.group("d")); y = int(m.group("y")); y = y+2000 if y<50 else (y+1900 if y<100 else y)
        month = _month_from_text(m.group("m"))
        return date(y, month, d) if month else None
    except Exception:
        return None

def extract_fecha(text: str) -> Optional[date]:
    m1 = FECHA_RE_NUM.search(text or "")
    if m1:
        d = _parse_date_numeric(m1.group(1))
        if d: return d
    for m in FECHA_RE_TXT.finditer(text or ""):
        dt = _parse_date_textual(m)
        if dt: return dt
    return None
