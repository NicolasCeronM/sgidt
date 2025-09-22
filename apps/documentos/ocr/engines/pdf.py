# -*- coding: utf-8 -*-
from pdfminer.high_level import extract_text

def read_pdf_text(path: str) -> str | None:
    try:
        txt = extract_text(path)
        return txt if txt and txt.strip() else None
    except Exception:
        return None
