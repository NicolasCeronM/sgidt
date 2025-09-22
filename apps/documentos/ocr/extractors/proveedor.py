# -*- coding: utf-8 -*-
import re
from ..utils.text_norm import normalize_text
from ..utils.rut import clean_rut, is_valid as rut_is_valid

RE_RUT = re.compile(r"\b\d{1,2}\.?\d{3}\.?\d{3}\s*-\s*[0-9Kk]\b")

# Etiquetas y palabras que NO son razón social
STOP_WORDS = {
    "FACTURA","ELECTRONICA","ELECTRÓNICA","BOLETA","NOTA","CREDITO","CRÉDITO",
    "CEDIBLE","GIRO","S.I.I.","SII","EMISION","EMISIÓN","VENCIMIENTO","CONTACTO",
    "DIRECCION","DIRECCIÓN","R.U.T.","RUT","CIUDAD","COMUNA","TIPO","COMPRA",
    "SEÑOR(ES):","SEÑORES:"
}
# Indicadores de línea de dirección (evitar como nombre)
ADDR_HINTS = ("AVDA","AVENIDA","AV.","CALLE","PASAJE","PASaje","OF.","OFICINA",
              "N°","NUM","PROVIDENCIA","SANTIAGO","RENCA","COMUNA","CIUDAD","DEPTO","DEPARTAMENTO","REGIÓN","REGION","RAÚL","LABBÉ","LABBE")

def _is_label_line(s: str) -> bool:
    t = normalize_text(s)
    if not t or len(t) < 3:
        return True
    if t.endswith(":"):
        return True
    first = t.split()[0]
    return first in STOP_WORDS

def _looks_like_address(s: str) -> bool:
    t = normalize_text(s)
    if any(h in t for h in ADDR_HINTS): 
        return True
    if "," in s:                        # “PROVIDENCIA, SANTIAGO”
        return True
    if any(ch.isdigit() for ch in s):   # números típicos de dirección
        # pero permitimos dígito si es parte de “SPA”, etc. -> aquí lo cortamos duro
        return True
    return False

def _good_name(s: str) -> bool:
    if not s: 
        return False
    if _is_label_line(s): 
        return False
    if _looks_like_address(s): 
        return False
    t = normalize_text(s)
    return len(t) >= 6 and not any(ch.isdigit() for ch in t)

def extract_emisor_receptor(text: str):
    lines = [ln for ln in (text or "").splitlines()]
    n = len(lines)
    linesN = [normalize_text(ln) for ln in lines]

    # Delimitamos el bloque del receptor “SEÑOR(ES) …”
    idx_senor = None
    for i, ln in enumerate(linesN):
        if "SEÑOR" in ln or "RECEPTOR" in ln:
            idx_senor = i
            break

    # Ventana acotada para buscar datos del receptor
    receptor_block = range(idx_senor or 0, min(n, (idx_senor or 0) + 16))

    # ---------- Nombre emisor ----------
    # Heurística: primer nombre “bueno” antes del bloque de receptor.
    head_end = (idx_senor or min(80, n))
    emisor_nombre = None
    for i in range(head_end):
        ln = lines[i].strip()
        if _good_name(ln):
            emisor_nombre = normalize_text(ln)
            break
    # fallback: busca el nombre más largo “bueno” en las primeras 80 líneas
    if not emisor_nombre:
        cands = [normalize_text(lines[i]) for i in range(min(n, 80)) if _good_name(lines[i])]
        if cands:
            emisor_nombre = max(cands, key=len)

    # ---------- RUT emisor ----------
    emisor_rut = None
    for i in range(0, head_end):
        m = RE_RUT.search(lines[i])
        if not m: 
            continue
        r = clean_rut(m.group(0))
        if rut_is_valid(r):
            emisor_rut = r
            break
    # 2) Si no aparece ahí (como en Jirafa), busca fuera del bloque del receptor
    if not emisor_rut:
        for i in range(head_end, n):
            if idx_senor is not None and i in receptor_block:
                continue
            m = RE_RUT.search(lines[i])
            if not m:
                continue
            r = clean_rut(m.group(0))
            if rut_is_valid(r):
                emisor_rut = r
                break

    # ---------- Receptor ----------
    receptor_nombre = None
    receptor_rut = None
    if idx_senor is not None:
        if idx_senor + 1 < n and _good_name(lines[idx_senor + 1]):
            receptor_nombre = normalize_text(lines[idx_senor + 1])
        win = " ".join(lines[idx_senor: min(n, idx_senor + 12)])
        m2 = RE_RUT.search(win)
        if m2:
            receptor_rut = clean_rut(m2.group(0))

    return (
        {"rut": emisor_rut, "nombre": emisor_nombre},
        {"rut": receptor_rut, "nombre": receptor_nombre},
    )
