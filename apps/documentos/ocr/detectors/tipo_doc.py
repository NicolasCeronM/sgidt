# -*- coding: utf-8 -*-
from ..patterns import TIPOS_PALABRAS

def guess_tipo(text: str) -> str:
    up = (text or "").upper()
    for tipo, palabras in TIPOS_PALABRAS.items():
        if any(p in up for p in palabras):
            return tipo
    return "desconocido"
