# apps/documentos/ocr/utils/rut.py
# -*- coding: utf-8 -*-
import re

def clean_rut(rut: str) -> str:
    if not rut: return ""
    rut = rut.strip().upper()
    rut = rut.replace(" ", "").replace(".", "")
    if "-" not in rut and len(rut) > 1:
        rut = rut[:-1] + "-" + rut[-1]
    return rut

def dv_calc(num: int) -> str:
    s, m = 0, 2
    for d in reversed(str(num)):
        s += int(d) * m
        m = 2 if m == 7 else m + 1
    r = 11 - (s % 11)
    return "0" if r == 11 else "K" if r == 10 else str(r)

def is_valid(rut: str) -> bool:
    rut = clean_rut(rut)
    m = re.match(r"^(\d+)-([0-9K])$", rut)
    if not m: return False
    num, dv = int(m.group(1)), m.group(2)
    return dv == dv_calc(num)

def format_rut(rut: str) -> str:
    rut_limpio = clean_rut(rut)
    if not rut_limpio or not is_valid(rut_limpio): return ""
    cuerpo, dv = rut_limpio.split('-')
    try:
        cuerpo_formateado = f"{int(cuerpo):,}".replace(",", ".")
        return f"{cuerpo_formateado}-{dv}"
    except (ValueError, TypeError):
        return rut_limpio