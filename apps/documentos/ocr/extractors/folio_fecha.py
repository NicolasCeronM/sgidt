# -*- coding: utf-8 -*-
from ..utils import patterns, dates

def extract_folio(text: str):
    folio = None; conf = 0.4
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if patterns.ANCHOR_FACTURA.search(ln):
            window = " ".join(lines[i:i+4])
            m = patterns.RE_FOLIO.search(window)
            if m:
                try:
                    folio = int(m.group(1)); conf = 0.9; break
                except: pass
    if not folio:
        m = patterns.RE_FOLIO.search(text)
        if m:
            try: folio = int(m.group(1)); conf = 0.6
            except: pass
    return folio, conf

def extract_fecha(text: str):
    # 1) Recorre línea por línea para agarrar el caso "misma línea"
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if patterns.ANCHOR_FECHA.search(ln):
            # mismo renglón
            dt = dates.parse_date_any(ln)
            if dt: return dt.isoformat(), 0.95
            # ventana corta hacia adelante por si el proveedor lo corta
            window = " ".join(lines[i:i+3])
            dt2 = dates.parse_date_any(window)
            if dt2: return dt2.isoformat(), 0.9

    # 2) Fallback global: cualquier fecha con formato '01 de Septiembre del 2025' o '01/09/2025'
    dtg = dates.parse_date_any(text)
    return (dtg.isoformat(), 0.7) if dtg else (None, 0.0)
