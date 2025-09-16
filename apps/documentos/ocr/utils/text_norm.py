# -*- coding: utf-8 -*-
import unicodedata

def preprocess_text(text: str) -> str:
    text = (text or "")
    text = text.replace("\u00A0", " ").replace("\u2007", " ").replace("\u202F", " ")
    text = (text.replace("\u2212","-").replace("\u2010","-").replace("\u2011","-")
                 .replace("\u2012","-").replace("\u2013","-").replace("\u2014","-"))
    text = text.replace(" :", ":").replace(": ", ": ")
    return text

def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn")
