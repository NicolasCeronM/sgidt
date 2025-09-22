# -*- coding: utf-8 -*-
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.core.files.storage import default_storage
from django.conf import settings
import logging
import json
import os

from apps.documentos.models import Documento
from apps.documentos.ocr import parse_document  # orquestador OCR

log = logging.getLogger(__name__)

def _set_if_has_attr(obj, field, value):
    """Asigna si el modelo tiene el atributo (para tolerar columnas opcionales)."""
    if hasattr(obj, field):
        setattr(obj, field, value)

@shared_task(bind=True, max_retries=0, default_retry_delay=10)
def extract_document(self, documento_id: int):
    """
    Toma un Documento recién subido, corre el OCR/parsers y persiste los campos.
    Reintentos desactivados por defecto para no duplicar trabajo.
    """
    try:
        doc = Documento.objects.get(pk=documento_id)
    except Documento.DoesNotExist:
        log.error("Documento %s no existe", documento_id)
        return

    # Ruta absoluta del archivo
    path = doc.archivo.path if hasattr(doc.archivo, "path") else default_storage.path(doc.archivo.name)

    try:
        parsed = parse_document(path) or {}
    except Exception as e:
        log.exception("Error parseando documento %s: %s", documento_id, e)
        with transaction.atomic():
            doc.estado = "error"
            _set_if_has_attr(doc, "ocr_json", {"error": str(e)})
            doc.save(update_fields=["estado"])
        return

    # Mapear y guardar
    try:
        with transaction.atomic():
            # Tipo / folio / fecha
            doc.tipo_documento = (parsed.get("tipo_dte") or "desconocido")
            doc.folio = parsed.get("folio")
            doc.fecha_emision = parsed.get("fecha_emision")  # string 'YYYY-MM-DD' o date; Django lo acepta

            # Emisor
            doc.rut_proveedor = parsed.get("emisor_rut")
            doc.razon_social_proveedor = parsed.get("emisor_nombre")

            # Montos (usar SIEMPRE el monto de IVA, no la tasa)
            doc.monto_neto = parsed.get("monto_neto") or 0
            doc.monto_exento = parsed.get("monto_exento") or 0
            doc.iva = parsed.get("iva_monto") or 0
            doc.total = parsed.get("total") or 0

            # Estado local
            doc.estado = "procesado"

            # Guardar dump OCR para depuración si tu modelo lo tiene
            dbg = {
                "engine_version": parsed.get("_engine_version"),
                "source": parsed.get("_source"),
                "confidences": parsed.get("confidences"),
                "debug": parsed.get("_debug"),
                "raw_text": parsed.get("_raw_text"),
                "parsed": {
                    "tipo_dte": parsed.get("tipo_dte"),
                    "folio": parsed.get("folio"),
                    "fecha_emision": parsed.get("fecha_emision"),
                    "emisor_rut": parsed.get("emisor_rut"),
                    "emisor_nombre": parsed.get("emisor_nombre"),
                    "monto_neto": parsed.get("monto_neto"),
                    "monto_exento": parsed.get("monto_exento"),
                    "iva_monto": parsed.get("iva_monto"),
                    "iva_tasa": parsed.get("iva_tasa"),
                    "total": parsed.get("total"),
                }
            }
            _set_if_has_attr(doc, "ocr_json", dbg)

            # Si tienes flags de validación SII, déjalos por ahora como default
            if hasattr(doc, "validado_sii") and doc.validado_sii is None:
                doc.validado_sii = False

            doc.save()
            log.info("Documento %s procesado OK (tipo=%s folio=%s total=%s)",
                     documento_id, doc.tipo_documento, doc.folio, doc.total)

    except Exception as e:
        log.exception("Error guardando documento %s: %s", documento_id, e)
        with transaction.atomic():
            doc.estado = "error"
            _set_if_has_attr(doc, "ocr_json", {"error": str(e), "partial": parsed})
            doc.save(update_fields=["estado"])

    return
