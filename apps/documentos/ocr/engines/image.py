# apps/documentos/ocr/engines/image.py
# -*- coding: utf-8 -*-
import pytesseract
from pdf2image import convert_from_path
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter

def _preprocess_pil(img: Image.Image) -> Image.Image:
    # Escala de grises + binarización suave + nitidez
    g = ImageOps.grayscale(img)
    # Aumenta contraste y reduce ruido leve
    g = g.filter(ImageFilter.MedianFilter(size=3))
    # Suaviza y realza bordes de texto
    g = g.filter(ImageFilter.UnsharpMask(radius=1, percent=160, threshold=3))
    return g

def read_raster_text(path: str) -> str:
    p = Path(path)
    images = []
    if p.suffix.lower() == ".pdf":
        # 350–400 DPI es buen punto medio; sube si algún emisor sale débil
        pages = convert_from_path(path, dpi=350)
        images.extend(pages)
    else:
        images.append(Image.open(path))

    result = []
    for img in images:
        proc = _preprocess_pil(img)
        txt = pytesseract.image_to_string(
            proc,
            lang="spa",                   # instala tesseract-ocr-spa
            config="--oem 3 --psm 6"      # bloques de texto uniforme
        )
        result.append(txt)
    return "\n".join(result)
