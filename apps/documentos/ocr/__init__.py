# Punto de entrada público del OCR
import mimetypes
import logging
from .schema import OCRResult
from .engines.pdf import text_from_pdf
from .engines.image import text_from_image
from .parsing import parse_text

log = logging.getLogger(__name__)

def parse_file(path: str, mime: str | None = None) -> dict:
    mime = mime or (mimetypes.guess_type(path)[0] or "")
    if mime.startswith("application/pdf") or path.lower().endswith(".pdf"):
        raw = text_from_pdf(path)
        fuente = "pdf_text" if len((raw or '').strip()) > 40 else "pdf_ocr"
    elif mime.startswith("image/"):
        raw = text_from_image(path)
        fuente = "image_ocr"
    else:
        raw = text_from_pdf(path) if path.lower().endswith(".pdf") else ""
        fuente = "pdf_text" if len((raw or '').strip()) > 40 else "unknown"

    res: OCRResult = parse_text(raw or "")
    res.fuente_texto = fuente
    log.info("OCR parse_file: tipo=%s, rut=%s, folio=%s, fecha=%s, total=%s",
             res.tipo_documento, res.rut_proveedor, res.folio, res.fecha_emision, res.total)
    return res.to_dict()

__all__ = ["parse_file"]  # <- export explícito
