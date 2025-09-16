# -*- coding: utf-8 -*-
import logging
import pytesseract
from PIL import Image, ImageOps, ImageFilter
from ..config import settings

log = logging.getLogger(__name__)

if settings.TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

def text_from_image(path: str) -> str:
    try:
        im = Image.open(path)
        im = ImageOps.exif_transpose(im).convert("L").filter(ImageFilter.MedianFilter(3))
        return pytesseract.image_to_string(
            im, lang=settings.TESSERACT_LANG,
            config=f"--psm {settings.TESSERACT_PSM_IMAGE} --oem {settings.TESSERACT_OEM}",
        )
    except Exception as e:
        log.error("Fallo OCR imagen: %s", e)
        return ""
