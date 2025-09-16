# -*- coding: utf-8 -*-
import re
from ..patterns import RUT_RE

RUT_LINE_RE = re.compile(r"\bR\.?\s*U\.?\s*T\.?|RUT", re.IGNORECASE)

def all_ruts_with_pos(text: str):
    outs = []
    for m in RUT_RE.finditer(text):
        cuerpo, dv = m.group(1), m.group(2)
        rut = f"{cuerpo}-{dv}".replace(" ", "")
        outs.append((rut, m.start()))
    return outs

def line_has_rut(line: str) -> bool:
    return bool(RUT_LINE_RE.search(line))
