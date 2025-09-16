# -*- coding: utf-8 -*-
from .schema import OCRResult
from .utils.text_norm import preprocess_text
from .detectors.tipo_doc import guess_tipo
from .detectors.iva_rate import guess_iva_rate
from .extractors.folio_fecha import extract_folio, extract_fecha
from .extractors.proveedor import select_rut_proveedor, extract_proveedor_nombre
from .extractors.amounts import parse_montos

def parse_text(raw_text: str) -> OCRResult:
    text = preprocess_text(raw_text or "")
    tipo = guess_tipo(text)
    iva_rate = guess_iva_rate(text) or 19

    rut = (select_rut_proveedor(text) or "").replace(".", "").upper()
    folio = extract_folio(text) or ""
    fecha = extract_fecha(text)
    proveedor = extract_proveedor_nombre(text.splitlines(), rut)

    montos = parse_montos(text, tipo, iva_rate)

    return OCRResult(
        raw_text=text,
        rut_proveedor=rut,
        proveedor_nombre=proveedor or "",
        folio=folio or "",
        fecha_emision=fecha,
        tipo_documento=tipo,
        iva_tasa=iva_rate,
        **montos,
        fuente_texto="unknown",
    )
