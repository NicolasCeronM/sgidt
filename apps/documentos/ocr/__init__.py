# -*- coding: utf-8 -*-
from .engines.pdf import read_pdf_text
from .engines.image import read_raster_text
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
    iva_rate_pdf = amounts_pdf.get("iva_tasa") or detect_iva_rate(text_pdf or "")

    # ---- ¿Faltan campos críticos? Si sí, OCR al PDF rasterizado ----
    need_ocr = (not fecha_pdf) or (amounts_pdf.get("total") in (None, 0))
    need_ocr = need_ocr or (not emisor_pdf.get("rut")) or (not folio_pdf)

    text_ocr = None
    if need_ocr or not text_pdf:
        text_ocr = read_raster_text(path)
        debug.append("tesseract_ok")
    else:
        debug.append("tesseract_skipped")

    # Extrae desde OCR si lo corrimos
    tipo_dte_ocr = tipo_desc_ocr = None
    folio_ocr = c_folio_ocr = None
    fecha_ocr = c_fecha_ocr = None
    emisor_ocr = receptor_ocr = {}
    amounts_ocr = {}
    iva_rate_ocr = None

    if text_ocr:
        tipo_dte_ocr, tipo_desc_ocr = detect_tipo_dte(text_ocr or "")
        folio_ocr, c_folio_ocr = extract_folio(text_ocr or "")
        fecha_ocr, c_fecha_ocr = extract_fecha(text_ocr or "")
        emisor_ocr, receptor_ocr = extract_emisor_receptor(text_ocr or "")
        amounts_ocr = extract_amounts(text_ocr or "")
        iva_rate_ocr = amounts_ocr.get("iva_tasa") or detect_iva_rate(text_ocr or "")

    # ---- FUSIÓN campo a campo ----
    tipo_dte = _merge(tipo_dte_pdf, tipo_dte_ocr)
    tipo_desc = _merge(tipo_desc_pdf, tipo_desc_ocr)
    folio = _merge(folio_pdf, folio_ocr)
    fecha = _merge(fecha_pdf, fecha_ocr)

    emisor_rut = _merge(emisor_pdf.get("rut") if emisor_pdf else None,
                        emisor_ocr.get("rut") if emisor_ocr else None)
    emisor_nombre = _merge(emisor_pdf.get("nombre") if emisor_pdf else None,
                           emisor_ocr.get("nombre") if emisor_ocr else None)
    receptor_rut = _merge(receptor_pdf.get("rut") if receptor_pdf else None,
                          receptor_ocr.get("rut") if receptor_ocr else None)
    receptor_nombre = _merge(receptor_pdf.get("nombre") if receptor_pdf else None,
                             receptor_ocr.get("nombre") if receptor_ocr else None)

    # Montos: prioriza PDF si están completos; si falta, usa OCR y reconcilia
    amounts = {
        "monto_neto": _merge(amounts_pdf.get("monto_neto"), amounts_ocr.get("monto_neto")),
        "monto_exento": _merge(amounts_pdf.get("monto_exento"), amounts_ocr.get("monto_exento")),
        "iva_monto": _merge(amounts_pdf.get("iva_monto"), amounts_ocr.get("iva_monto")),
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
        "_raw_text": (text_pdf or "") + ("\n\n" + text_ocr if text_ocr else ""),
        "_source": "pdf_text+pdf_ocr" if text_pdf and text_ocr else ("pdf_text" if text_pdf else "image_ocr"),
        "_engine_version": "",
        "_debug": debug,
    }

    doc = reconcile(doc)
    return doc
