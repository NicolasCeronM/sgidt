# -*- coding: utf-8 -*-
import re
from typing import Optional, List
from ..patterns import PROV_LINEUP_RE
from ..utils.rut import all_ruts_with_pos
from ..patterns import RUT_RE

def _find_first_pos(text: str, pattern: re.Pattern) -> int | None:
    m = pattern.search(text); return m.start() if m else None

def select_rut_proveedor(text: str) -> Optional[str]:
    ruts = all_ruts_with_pos(text or "")
    if not ruts: return None
    up = (text or "").upper()
    pos_senor = _find_first_pos(up, re.compile(r"\bSE[ÑN]OR(?:ES)?\b"))
    pos_fact = _find_first_pos(up, re.compile(r"\b(FACTURA|BOLETA|NOTA)\b"))
    candidatos = ruts
    if pos_senor is not None:
        candidatos = [rp for rp in candidatos if rp[1] < pos_senor] or candidatos
    if pos_fact is not None:
        arriba = [rp for rp in candidatos if rp[1] <= pos_fact]
        if arriba: candidatos = arriba
    candidatos.sort(key=lambda x: x[1])
    return candidatos[0][0] if candidatos else None

def _pretty_name(s: str) -> str:
    s = s.strip()
    s = re.sub(RUT_RE, "", s).strip(" -:|")
    s = re.sub(r"\s{2,}", " ", s)
    if s.isupper():
        sc = s.title()
        sc = re.sub(r"\b(Spa|Ltda|Eirl|E\.I\.R\.L|Eirl\.|S\.A\.?)\b", lambda m: m.group(0).upper(), sc)
        return sc
    return s

def extract_proveedor_nombre(lines: List[str], rut: Optional[str]) -> Optional[str]:
    joined = "\n".join(lines)
    pos_senor = _find_first_pos(joined.upper(), re.compile(r"\bSE[ÑN]OR(?:ES)?\b"))
    cut_index = None
    if pos_senor is not None:
        acc = 0
        for i, ln in enumerate(lines):
            acc += len(ln) + 1
            if acc >= pos_senor:
                cut_index = i; break
    search_range = lines[:cut_index] if cut_index else lines

    for i, ln in enumerate(search_range):
        if PROV_LINEUP_RE.search(ln):
            after = ln.split(":")[-1].strip()
            cand = after or (search_range[i+1].strip() if i+1 < len(search_range) else "")
            cand = re.sub(r"[\*\#\|]+"," ", cand).strip()
            cand = re.sub(r"\s{2,}"," ", cand)
            if len(cand) > 2:
                return _pretty_name(cand)

    if rut:
        rut_clean = rut.replace(".", "")
        idx_rut = None
        for i, ln in enumerate(search_range):
            if rut_clean in ln.replace(".", ""):
                idx_rut = i; break
        if idx_rut is not None:
            for j in range(max(0, idx_rut-3), idx_rut+1):
                cand = search_range[j].strip()
                if len(cand) > 3 and not re.search(r"\b(FACTURA|BOLETA|NOTA|RUT|R\.U\.T|FOLIO|SII|ELECTR[ÓO]NICA)\b", cand, re.IGNORECASE):
                    return _pretty_name(cand)

    for cand in search_range[:15]:
        c = cand.strip()
        if len(c) >= 6 and (c.isupper() or " SPA" in c or " LTDA" in c or " S.A" in c):
            if not re.search(r"\b(FACTURA|BOLETA|NOTA|RUT|R\.U\.T|FOLIO|SII|ELECTR[ÓO]NICA)\b", c, re.IGNORECASE):
                return _pretty_name(c)
    return None
