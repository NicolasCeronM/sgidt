# -*- coding: utf-8 -*-
"""
Normaliza y reconcilia los campos extraídos por el OCR/parsers.
- Limpia RUT y razón social
- Asegura que los montos sean coherentes (neto + exento + iva = total)
- Infieren tipo de documento por montos si el detector textual no lo resolvió
- Normaliza fecha a YYYY-MM-DD (string) si viene como date/datetime
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime
from ..utils.rut import clean_rut, is_valid as rut_is_valid
from ..utils.text_norm import normalize_text

def _D(x):
    try:
        return Decimal(str(x))
    except Exception:
        return Decimal("0")

def _clamp_nonneg(x):
    d = _D(x)
    return d if d >= 0 else Decimal("0")

def _round0(x):
    return _D(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

def _clean_name(n):
    if not n:
        return None
    # Normaliza (quita acentos y pasa a mayúsculas)
    t = normalize_text(str(n))
    # Evita etiquetas frecuentes
    STOP = {"FACTURA", "ELECTRONICA", "ELECTRÓNICA", "BOLETA", "NOTA", "CRÉDITO",
            "CREDITO", "CEDIBLE", "GIRO", "R.U.T.", "RUT", "DIRECCION", "DIRECCIÓN",
            "CIUDAD", "COMUNA", "TIPO", "COMPRA", "SEÑOR(ES):", "SEÑORES:", "EMISION",
            "EMISIÓN", "VENCIMIENTO", "CONTACTO"}
    words = [w for w in t.split() if w not in STOP]
    t2 = " ".join(words).strip()
    return t2 or None

def _clean_fecha(f):
    if not f:
        return None
    if isinstance(f, date):
        return f.isoformat()
    if isinstance(f, datetime):
        return f.date().isoformat()
    # ya es string
    s = str(f).strip()
    # si viniera "YYYY-MM-DD HH:MM", nos quedamos con la fecha
    if " " in s and len(s.split(" ")[0]) == 10:
        return s.split(" ")[0]
    return s

def reconcile(doc: dict) -> dict:
    if not doc:
        return {}

    # ---------- RUT / Razón social ----------
    rut = doc.get("emisor_rut")
    if rut:
        rut = clean_rut(str(rut))
        if rut_is_valid(rut):
            doc["emisor_rut"] = rut
        else:
            # si no es válido, preferimos dejarlo vacío antes que malo
            doc["emisor_rut"] = None

    nombre = _clean_name(doc.get("emisor_nombre"))
    doc["emisor_nombre"] = nombre

    # ---------- Fechas ----------
    doc["fecha_emision"] = _clean_fecha(doc.get("fecha_emision"))

    # ---------- Montos ----------
    neto   = _clamp_nonneg(doc.get("monto_neto"))
    exento = _clamp_nonneg(doc.get("monto_exento"))
    iva    = _clamp_nonneg(doc.get("iva_monto"))
    total  = _clamp_nonneg(doc.get("total"))

    # Si falta total pero están los otros, lo calculamos
    if total == 0 and (neto > 0 or exento > 0 or iva > 0):
        total = neto + exento + iva

    # Si falta IVA pero hay neto y total, lo inferimos
    if iva == 0 and total > 0 and (neto > 0 or exento > 0):
        calc_iva = total - (neto + exento)
        if calc_iva >= 0:
            iva = calc_iva

    # Si falta neto pero hay total e IVA
    if neto == 0 and total > 0 and iva >= 0:
        neto = total - exento - iva
        if neto < 0:
            neto = Decimal("0")

    # Redondeo entero CLP
    neto   = _round0(neto)
    exento = _round0(exento)
    iva    = _round0(iva)
    total  = _round0(total)

    doc["monto_neto"]   = int(neto)
    doc["monto_exento"] = int(exento)
    doc["iva_monto"]    = int(iva)
    doc["total"]        = int(total)

    # Guardar tasa si viene (no es obligatoria)
    iva_tasa = doc.get("iva_tasa")
    if iva_tasa:
        try:
            doc["iva_tasa"] = float(iva_tasa)
        except Exception:
            doc["iva_tasa"] = None

    # ---------- Tipo de documento ----------
    t = doc.get("tipo_dte") or "desconocido"
    # Reglas por montos si sigue desconocido
    if t == "desconocido":
        if iva > 0:
            t = "factura_afecta"
            doc["tipo_desc"] = "Factura Electrónica"
        elif exento > 0:
            t = "factura_exenta"
            doc["tipo_desc"] = "Factura Electrónica Exenta"
    doc["tipo_dte"] = t

    return doc
