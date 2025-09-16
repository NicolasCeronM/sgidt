# -*- coding: utf-8 -*-
import re
from decimal import Decimal
from ..patterns import LABELS_MONTOS, MONEDA_RE
from ..utils.numbers import normalize_amount, round0
from ..utils.rut import line_has_rut

def _amounts_in_line(line: str):
    vals = []
    for m in MONEDA_RE.finditer(line or ""):
        v = normalize_amount(m.group(1))
        if v is not None:
            vals.append(v)
    return vals

def parse_montos(text: str, tipo: str, iva_rate: int | float) -> dict:
    lines = (text or "").splitlines()
    upper = [ln.upper() for ln in lines]
    out = {"monto_neto": None, "monto_exento": None, "iva": None, "total": None}

    # 1) Cercanía a etiquetas (ventana: -1 a +8 líneas)
    for key, pat in LABELS_MONTOS.items():
        r = re.compile(pat, re.IGNORECASE)
        for i, u in enumerate(upper):
            if r.search(u):
                cands = []
                for j in range(max(0, i-1), min(i+9, len(lines))):
                    if line_has_rut(lines[j]): 
                        continue
                    cands += _amounts_in_line(lines[j])
                if cands:
                    out[key] = (cands[-1] if key == "total" else max(cands))
                break

    # 2) Fallback para TOTAL: máximo global (ignorando líneas con RUT)
    if out["total"] is None:
        pool = []
        for ln in lines:
            if line_has_rut(ln): 
                continue
            pool += _amounts_in_line(ln)
        if pool:
            out["total"] = max(pool, key=lambda z: abs(z))

    # 3) Derivaciones y redondeos
    rate = Decimal(str(iva_rate)) / Decimal("100")
    if out["total"] is not None and out["iva"] is None:
        neto = out["monto_neto"]
        exento = out["monto_exento"] or Decimal("0")
        if neto is not None:
            iva_calc = out["total"] - neto - exento
            if abs(iva_calc) < Decimal("2"):
                iva_calc = (neto * rate).quantize(Decimal("1"))
            out["iva"] = iva_calc if iva_calc != 0 else None

    if out["monto_neto"] is None and out["total"] is not None:
        exento = out["monto_exento"] or Decimal("0")
        if out["iva"] is not None:
            out["monto_neto"] = out["total"] - exento - out["iva"]
        else:
            neto_est = (out["total"] - exento) / (Decimal("1") + rate)
            out["monto_neto"] = round0(neto_est)
            iva_est = out["total"] - exento - out["monto_neto"]
            out["iva"] = iva_est if abs(iva_est) > 0 else None

    for k in ("monto_neto", "iva", "total"):
        v = out[k]
        if v is not None:
            out[k] = round0(v)

    neto = out["monto_neto"] or Decimal("0")
    exento = out["monto_exento"] or Decimal("0")
    iva = out["iva"] or Decimal("0")
    total = out["total"]
    if total is not None:
        diff = total - (neto + exento + iva)
        if abs(diff) <= Decimal("2"):
            out["iva"] = round0(iva + diff)

    if tipo.startswith("nota_credito"):
        for k in out:
            if out[k] is not None and out[k] > 0:
                out[k] = -out[k]

    return out
