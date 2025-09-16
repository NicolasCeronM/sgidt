# -*- coding: utf-8 -*-
import logging
from pdfminer.high_level import extract_text
from pdf2image import convert_from_path
import pytesseract
from PIL import ImageOps, ImageFilter
from ..config import settings

log = logging.getLogger(__name__)

if settings.TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

def text_from_pdf(path: str) -> str:
    # 1) Intentar texto embebido
    try:
        text = extract_text(path) or ""
        if len(text.strip()) > 40:
            return text
    except Exception as e:
        log.warning("Fallo extract_text PDF: %s", e)

    # 2) Fallback: rasterizar y OCR
    try:
        images = convert_from_path(path, fmt="png", dpi=300, poppler_path=settings.POPPLER_PATH)
        parts = []
        for im in images:
            im = ImageOps.exif_transpose(im).convert("L").filter(ImageFilter.MedianFilter(3))
            parts.append(
                pytesseract.image_to_string(
                    im, lang=settings.TESSERACT_LANG,
                    config=f"--psm {settings.TESSERACT_PSM} --oem {settings.TESSERACT_OEM}"
                )
            )
        return "\n".join(parts)
    except Exception as e:
        log.error("Fallo OCR PDF: %s", e)
        return ""
