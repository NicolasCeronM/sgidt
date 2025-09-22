# -*- coding: utf-8 -*-
import re

NUM_MONEY = r"(?:\$?\s*)?([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]{1,2})?|[0-9]+)"
RE_MONEY  = re.compile(NUM_MONEY)

# Estricto con tolerancia a espacios alrededor del guion
RUT_STRICT = r"\b\d{1,2}\.?\d{3}\.?\d{3}\s*-\s*[0-9Kk]\b"
RUT_LOOSE  = r"\b\d{7,8}\s*-\s*[0-9Kk]\b"
RE_RUT_STRICT = re.compile(RUT_STRICT)
RE_RUT_LOOSE  = re.compile(RUT_LOOSE)

RE_FOLIO = re.compile(
    r"(?:\bFOLIO\b\s*[:#]?\s*|N[\u00B0\u00BA]?\s*|NO\.?\s*|#\s*)(\d{1,10})",
    re.I
)       

ANCHOR_FACTURA = re.compile(r"\bFACTURA\b", re.I)
ANCHOR_EXENTA  = re.compile(r"\bEXENTA\b", re.I)
ANCHOR_NC      = re.compile(r"NOTA\s+DE\s+CREDITO", re.I)
ANCHOR_FECHA   = re.compile(r"(Fecha\s+Emisi[oó]n?)", re.I)
ANCHOR_NETO    = re.compile(r"MONTO\s+NETO|\bNETO\b", re.I)
ANCHOR_IVA     = re.compile(r"\bI\.?V\.?A\.?\b|\bIVA\b", re.I)
ANCHOR_TOTAL   = re.compile(r"\bTOTAL\b", re.I)
ANCHOR_SENOR   = re.compile(r"SE[NÑ]OR\(ES\)", re.I)
ANCHOR_RUTLBL  = re.compile(r"R\.?\s*U\.?\s*T\.?\s*:?", re.I)
