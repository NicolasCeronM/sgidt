# apps/documentos/tasks/extract.py
from celery import shared_task
from django.apps import apps
from django.db import transaction
from django.utils.dateparse import parse_date
from decimal import Decimal
import os

from apps.documentos.ocr import parse_file as ocr_parse_file

def _to_decimal(v):
    if v is None or v == "": return None
    try: return Decimal(str(v))
    except Exception: return None

def _to_jsonable(obj):
    from datetime import date, datetime
    if isinstance(obj, Decimal): return float(obj)
    if isinstance(obj, (date, datetime)): return obj.isoformat()
    if isinstance(obj, dict): return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list): return [_to_jsonable(x) for x in obj]
    if isinstance(obj, tuple): return tuple(_to_jsonable(x) for x in obj)
    if isinstance(obj, set): return [_to_jsonable(x) for x in obj]
    return obj

@shared_task(name="documentos.extract_document", bind=True, max_retries=2, default_retry_delay=10)
def extract_document(self, documento_id: int):
    Documento = apps.get_model("documentos", "Documento")
    doc = Documento.objects.get(pk=documento_id)

    # marca procesando
    if doc.estado != "procesando":
        doc.estado = "procesando"
        doc.save(update_fields=["estado"])

    try:
        local_path = doc.archivo.path
        result = ocr_parse_file(local_path, doc.mime_type)


        # JSON crudo del OCR (serializable)
        doc.ocr_json = _to_jsonable(result)

        # Texto plano (si existe el campo en tu modelo)
        if hasattr(doc, "texto_plano"):
            doc.texto_plano = (result.get("raw_text") or "").strip()

        # Campos principales
        doc.tipo_documento = result.get("tipo_documento", "desconocido") or "desconocido"
        doc.folio = (result.get("folio") or "").strip()

        fe = result.get("fecha_emision")
        if isinstance(fe, str):
            fe = parse_date(fe)
        doc.fecha_emision = fe

        doc.rut_proveedor = (result.get("rut_proveedor") or "").replace(".", "").upper()
        doc.razon_social_proveedor = (result.get("proveedor_nombre") or "").strip()

        doc.iva_tasa = _to_decimal(result.get("iva_tasa"))
        doc.monto_neto = _to_decimal(result.get("monto_neto"))
        doc.monto_exento = _to_decimal(result.get("monto_exento"))
        doc.iva = _to_decimal(result.get("iva"))
        doc.total = _to_decimal(result.get("total"))

        # Metadatos OCR
        doc.ocr_fuente = result.get("fuente_texto") or ""
        doc.ocr_lang = os.getenv("TESSERACT_LANG", "spa+eng")
        doc.ocr_engine = "tesseract"
        doc.ocr_version = os.getenv("TESSERACT_VERSION", "")

        doc.estado = "procesado"
        doc.save()
        return {"ok": True, "documento_id": doc.pk, "estado": doc.estado}

    except Exception as e:
        try:
            doc.estado = "error"
            doc.save(update_fields=["estado"])
        except Exception:
            pass
        raise e
