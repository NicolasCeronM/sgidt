# -*- coding: utf-8 -*-
import unicodedata
import re

def preprocess_text(text: str) -> str:
    text = (text or "")
    text = text.replace("\u00A0", " ").replace("\u2007", " ").replace("\u202F", " ")
    text = (text.replace("\u2212","-").replace("\u2010","-").replace("\u2011","-")
                 .replace("\u2012","-").replace("\u2013","-").replace("\u2014","-"))
    text = text.replace(" :", ":").replace(": ", ": ")
    return text

def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn")

def normalize_text(text: str) -> str:
    """
    Normaliza texto para OCR:
      - Pasa a mayúsculas
      - Quita acentos
      - Colapsa espacios
      - Elimina caracteres no imprimibles
    """
    if not text:
        return ""
    # Quita acentos
    t = unicodedata.normalize("NFKD", text)
    t = "".join([c for c in t if not unicodedata.combining(c)])
    # Pone todo en mayúsculas
    t = t.upper()
    # Reemplaza múltiples espacios y limpia caracteres no deseados
    t = re.sub(r"\s+", " ", t)
    return t.strip()