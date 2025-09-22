# -*- coding: utf-8 -*-
import re
from ..utils import patterns, numbers

RE_PERCENT = re.compile(r"\b\d{1,2}\s*%")
RE_LABEL_NETO  = re.compile(r"\bNETO\b", re.I)
RE_LABEL_EXENTO= re.compile(r"\bEXENTO\b", re.I)
RE_LABEL_IVA   = re.compile(r"\bI\.?V\.?A\.?\b|\bIVA\b", re.I)
RE_LABEL_TOTAL = re.compile(r"\bTOTAL\b", re.I)

def _money_list(line: str):
    vals = []
    for m in patterns.RE_MONEY.findall(line or ""):
        v = numbers.to_int_money(m)
        if v is None: 
            continue
        if v >= 1000:  # evita confundir % o cantidades pequeñas
            vals.append(v)
    return vals

def _first_money_forward(lines, start, max_ahead=5, avoid_words=()):
    for k in range(start, min(len(lines), start + 1 + max_ahead)):
        L = lines[k]
        U = L.upper()
        if any(w in U for w in avoid_words): 
            continue
        if RE_PERCENT.search(L): 
            continue
        vals = _money_list(L)
        if vals:
            nz = [x for x in vals if x != 0]
            return max(nz) if nz else 0
    return None

def _try_four_label_block(lines, i_net):
    """
    Caso Jirafa: aparecen las 4 etiquetas (NETO, EXENTO, IVA, TOTAL) en bloque, 
    y luego en líneas siguientes aparecen 3 números: neto, exento y total.
    """
    n = len(lines)
    # buscamos las otras 3 etiquetas dentro de una ventana corta
    have = {"NETO": True}
    end = i_net
    for k in range(i_net+1, min(n, i_net+8)):
        u = lines[k].upper()
        if RE_LABEL_EXENTO.search(u): have["EXENTO"] = True
        if RE_LABEL_IVA.search(u):    have["IVA"]    = True
        if RE_LABEL_TOTAL.search(u):  have["TOTAL"]  = True; end = k
    if not all(k in have for k in ("EXENTO","IVA","TOTAL")):
        return None

    # Los valores suelen venir inmediatamente después de la última etiqueta
    nums = []
    for k in range(end, min(n, end+8)):
        vals = _money_list(lines[k])
        if vals:
            nums.extend(vals)
        if len(nums) >= 3:
            break
    if len(nums) >= 2:
        neto   = nums[0]
        exento = nums[1] if len(nums) >= 3 else 0
        total  = nums[-1]
        iva    = max(total - (neto + exento), 0)
        return {"monto_neto": neto, "monto_exento": exento,
                "iva_monto": iva, "total": total,
                "conf_neto": 0.95, "conf_iva": 0.9, "conf_total": 0.95}
    return None

def extract_amounts(text: str):
    lines = text.splitlines()
    neto = iva = total = exento = None
    conf_n = conf_i = conf_t = 0.0
    iva_rate = None

    # 1) Intento especial: bloque de 4 etiquetas (como Jirafa)
    for i, ln in enumerate(lines):
        if RE_LABEL_NETO.search(ln):
            block = _try_four_label_block(lines, i)
            if block:
                neto   = block["monto_neto"];   conf_n = block["conf_neto"]
                exento = block["monto_exento"]
                iva    = block["iva_monto"];    conf_i = block["conf_iva"]
                total  = block["total"];        conf_t = block["conf_total"]
                break

    # 2) Fallback general (mismo algoritmo que ya tenías, con filtros)
    if neto is None:
        for i, ln in enumerate(lines):
            U = ln.upper()
            if patterns.ANCHOR_NETO.search(U):
                v = _first_money_forward(lines, i, max_ahead=4, avoid_words=("EXENTO","IVA","TOTAL"))
                if v is not None: neto, conf_n = v, 0.9
            if "EXENTO" in U and exento is None:
                v = _first_money_forward(lines, i, max_ahead=4, avoid_words=("NETO","IVA","TOTAL"))
                if v is not None: exento = v
            if patterns.ANCHOR_IVA.search(U):
                from ..utils.numbers import safe_rate
                r = safe_rate(ln)
                if r: iva_rate = r
                v = _first_money_forward(lines, i, max_ahead=4, avoid_words=("ADICIONAL","TOTAL"))
                if v is not None: iva, conf_i = v, 0.9
            if patterns.ANCHOR_TOTAL.search(U):
                v = _first_money_forward(lines, i, max_ahead=5)
                if v is not None: total, conf_t = v, 0.95

    # 3) Reconciliación
    if iva is None and neto is not None and total is not None:
        iva = max(total - (neto + (exento or 0)), 0); conf_i = max(conf_i, 0.85)
    if neto is None and total is not None and iva is not None:
        neto = max(total - (iva + (exento or 0)), 0); conf_n = max(conf_n, 0.85)
    if iva_rate is None and iva is not None and neto:
        iva_rate = round(iva / max(neto, 1), 2)

    return {
        "monto_neto": neto, "conf_neto": conf_n,
        "monto_exento": exento,
        "iva_monto": iva,   "conf_iva": conf_i,
        "iva_tasa": iva_rate,
        "total": total,     "conf_total": conf_t,
    }
