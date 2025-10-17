# -*- coding: utf-8 -*-
from .engines.pdf import read_pdf_text
from .engines.image import ocr_from_image_path as read_raster_text
from .extractors.folio_fecha import extract_folio, extract_fecha
from .extractors.amounts import extract_amounts
from .extractors.proveedor import extract_emisor_receptor
from .detectors.tipo_doc import detect_tipo_dte
from .detectors.iva_rate import detect_iva_rate
from .postprocess.reconcile import reconcile

def _merge(a, b):
    """Devuelve a si a tiene valor, si no b."""
    return a if (a is not None and a != "" and a != 0) else b

def parse_document(path: str) -> dict:
    debug = []
    # ---- PASO 1: PDF nativo (pdfminer) ----
    text_pdf = read_pdf_text(path)
    source = "pdf_text" if text_pdf else None
    if text_pdf:
        debug.append("pdfminer_ok")
    else:
        debug.append("pdfminer_empty")

    # Extrae desde texto PDF (si existe)
    tipo_dte_pdf, tipo_desc_pdf = detect_tipo_dte(text_pdf or "")
    folio_pdf, c_folio_pdf = extract_folio(text_pdf or "")
    fecha_pdf, c_fecha_pdf = extract_fecha(text_pdf or "")
    emisor_pdf, receptor_pdf = extract_emisor_receptor(text_pdf or "")
    amounts_pdf = extract_amounts(text_pdf or "")
    iva_rate_pdf = detect_iva_rate(text_pdf or "")

    # ---- PASO 2: OCR Tesseract (si no hay texto PDF o para validar) ----
    text_ocr = None
    if not text_pdf:
        text_ocr = read_raster_text(path)
        source = "ocr"
        if text_ocr:
            debug.append("tesseract_ok")
        else:
            debug.append("tesseract_empty")

    # Extrae desde texto OCR (si existe)
    tipo_dte_ocr, tipo_desc_ocr = detect_tipo_dte(text_ocr or "")
    folio_ocr, c_folio_ocr = extract_folio(text_ocr or "")
    fecha_ocr, c_fecha_ocr = extract_fecha(text_ocr or "")
    emisor_ocr, receptor_ocr = extract_emisor_receptor(text_ocr or "")
    amounts_ocr = extract_amounts(text_ocr or "")
    iva_rate_ocr = detect_iva_rate(text_ocr or "")

    # ---- PASO 3: Unificar resultados ----
    tipo_dte = _merge(tipo_dte_pdf, tipo_dte_ocr)
    tipo_desc = _merge(tipo_desc_pdf, tipo_desc_ocr)
    folio = _merge(folio_pdf, folio_ocr)
    fecha = _merge(fecha_pdf, fecha_ocr)
    emisor_rut = _merge(emisor_pdf.get("rut"), emisor_ocr.get("rut"))
    emisor_nombre = _merge(emisor_pdf.get("nombre"), emisor_ocr.get("nombre"))
    receptor_rut = _merge(receptor_pdf.get("rut"), receptor_ocr.get("rut"))
    receptor_nombre = _merge(receptor_pdf.get("nombre"), receptor_ocr.get("nombre"))

    amounts = {
        "monto_neto": _merge(amounts_pdf.get("neto"), amounts_ocr.get("neto")),
        "monto_exento": _merge(amounts_pdf.get("exento"), amounts_ocr.get("exento")),
        "iva_monto": _merge(amounts_pdf.get("iva"), amounts_ocr.get("iva")),
        "total": _merge(amounts_pdf.get("total"), amounts_ocr.get("total")),
        "conf_neto": _merge(amounts_pdf.get("conf_neto"), amounts_ocr.get("conf_neto")),
        "conf_iva": _merge(amounts_pdf.get("conf_iva"), amounts_ocr.get("conf_iva")),
        "conf_total": _merge(amounts_pdf.get("conf_total"), amounts_ocr.get("conf_total")),
        "iva_tasa": _merge(iva_rate_pdf, iva_rate_ocr),
    }

    doc = {
        "tipo_dte": tipo_dte,
        "tipo_desc": tipo_desc,
        "folio": folio,
        "fecha_emision": fecha,
        "emisor_rut": emisor_rut,
        "emisor_nombre": emisor_nombre,
        "receptor_rut": receptor_rut,
        "receptor_nombre": receptor_nombre,
        "monto_neto": amounts.get("monto_neto"),
        "monto_exento": amounts.get("monto_exento"),
        "iva_monto": amounts.get("iva_monto"),
        "iva_tasa": amounts.get("iva_tasa"),
        "total": amounts.get("total"),
        "confidences": {
            "folio": _merge(c_folio_pdf, c_folio_ocr),
            "fecha": _merge(c_fecha_pdf, c_fecha_ocr),
            "neto": amounts.get("conf_neto"),
            "iva": amounts.get("conf_iva"),
            "total": amounts.get("conf_total"),
        },
        "raw_text": text_ocr or text_pdf or "",
        "source": source,
        "debug": debug,
    }
    return reconcile(doc)