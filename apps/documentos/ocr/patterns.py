# -*- coding: utf-8 -*-
import re

RUT_RE = re.compile(r"(?<!\w)(\d{1,2}\.?(?:\d{3}\.)?\d{3})-\s*([\dkK])(?!\w)")
FOLIO_RE = re.compile(r"(?:FOLIO|Nº|N°|No\.?|Nro\.?|FOL\.?)[\s:]*([0-9]{3,})", re.IGNORECASE)
FECHA_RE_NUM = re.compile(r"\b(\d{1,2}[\/\.-]\d{1,2}[\/\.-]\d{2,4}|\d{4}[\/\.-]\d{1,2}[\/\.-]\d{1,2})\b")
FECHA_RE_TXT = re.compile(
    r"\b(?P<d>\d{1,2})\s*(?:de|del|-|/)?\s*(?P<m>[A-Za-zÁÉÍÓÚÜÑáéíóúüñ\.]{3,})\.?\s*(?:de|del|-|/)?\s*(?P<y>\d{2,4})\b",
    re.IGNORECASE
)

MESES = {
    "enero":1,"ene":1,"febrero":2,"feb":2,"marzo":3,"mar":3,"abril":4,"abr":4,"mayo":5,"may":5,
    "junio":6,"jun":6,"julio":7,"jul":7,"agosto":8,"ago":8,"septiembre":9,"setiembre":9,"sep":9,"set":9,
    "octubre":10,"oct":10,"noviembre":11,"nov":11,"diciembre":12,"dic":12,
}

MONEDA_RE = re.compile(r"\$?\s*(-?[0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]{2})?)")

LABELS_MONTOS = {
    "monto_neto":   r"\b(NETO|AFECTO|SUBTOTAL)\b",
    "monto_exento": r"\b(EXENTO)\b",
    "iva":          r"\b(I\.?V\.?A\.?|IVA)\b",
    "total":        r"\b(TOTAL)(?:\s+A\s+PAGAR|\s+PAGO)?\b",
}

TIPOS_PALABRAS = {
    "factura_afecta": ["FACTURA ELECTRÓNICA", "FACTURA A", "FACTURA"],
    "factura_exenta": ["FACTURA EXENTA"],
    "boleta_afecta":  ["BOLETA ELECTRÓNICA", "BOLETA"],
    "boleta_exenta":  ["BOLETA EXENTA"],
    "nota_credito":   ["NOTA DE CRÉDITO", "NC ELECTRÓNICA", "NOTA CREDITO"],
}

IVA_RATE_RE = re.compile(r"IVA[^0-9%]*(\d{1,2})\s*%")
PROV_KEYS = [
    r"\bRAZ[ÓO]N\s+SOCIAL\b",
    r"\bSE[ÑN]OR(?:ES)?\b",
    r"\bPROVEEDOR(?:A)?\b",
    r"\bEMISOR\b",
    r"\bVENDEDOR\b",
]
PROV_LINEUP_RE = re.compile("|".join(PROV_KEYS), re.IGNORECASE)
