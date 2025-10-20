# apps/documentos/tasks/extract.py

from celery import shared_task
from django.db import transaction
import logging

from apps.documentos.models import Documento
from apps.documentos.ocr import parse_document

log = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=0, default_retry_delay=10)
def extract_document(self, documento_id: int):
    """
    Toma un Documento, corre el OCR y persiste los campos extraídos.
    """
    try:
        doc = Documento.objects.get(pk=documento_id)
        doc.estado = "procesando"
        doc.save(update_fields=['estado'])
    except Documento.DoesNotExist:
        log.error("Documento %s no existe al iniciar la tarea.", documento_id)
        return

    path = doc.archivo.path

    try:
        # 1. Llamar al orquestador del OCR que ya sabemos que funciona bien.
        parsed_result, raw_text = parse_document(path)

        with transaction.atomic():
            # Volvemos a cargar el documento para asegurar que no hay concurrencia
            doc_to_update = Documento.objects.get(pk=documento_id)
            doc_to_update.estado = "procesado"

            # 2. Asignar CUIDADOSAMENTE cada campo del resultado al modelo.
            # Esta es la parte que estaba fallando.
            doc_to_update.tipo_documento = parsed_result.tipo_documento
            doc_to_update.folio = parsed_result.folio
            doc_to_update.fecha_emision = parsed_result.fecha_emision
            doc_to_update.rut_proveedor = parsed_result.rut_proveedor
            doc_to_update.razon_social_proveedor = parsed_result.proveedor_nombre

            # Asignar montos que vimos que se extraen bien en la consola
            doc_to_update.monto_neto = parsed_result.monto_neto
            doc_to_update.monto_exento = parsed_result.monto_exento
            doc_to_update.iva = parsed_result.iva
            doc_to_update.total = parsed_result.total
            doc_to_update.iva_tasa = parsed_result.iva_tasa

            # 3. Guardar los campos de auditoría
            doc_to_update.texto_plano = raw_text
            doc_to_update.ocr_fuente = parsed_result.fuente_texto
            doc_to_update.ocr_engine = "Tesseract"
            doc_to_update.ocr_version = "5.x" # O la versión que tengas

            # 4. Guardar todos los campos en la base de datos
            doc_to_update.save()

            log.info(
                "Documento %s procesado y GUARDADO CORRECTAMENTE (Total: %s)",
                documento_id, doc_to_update.total
            )

    except Exception as e:
        log.exception("Error CRÍTICO al procesar o guardar el documento %s: %s", documento_id, e)
        # Revertir el estado a 'error'
        doc.estado = "error"
        doc.save(update_fields=['estado'])