# apps/documentos/tasks/extract.py

from celery import shared_task
from django.db import transaction
import logging
from decimal import Decimal

from apps.documentos.models import Documento
from apps.sii.tasks import check_and_kickoff_sii

# Importamos los dos motores de extracción
from apps.documentos.ocr import parse_document  # Este es tu orquestador de OCR para PDFs
from apps.documentos.ocr.engines.xml import extract_data_from_xml # El nuevo parser de XML

log = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=0, default_retry_delay=10)
def extract_document(self, documento_id: int):
    """
    Toma un Documento, determina si es PDF o XML, extrae los datos
    usando el motor correspondiente y persiste los campos.
    """
    try:
        doc = Documento.objects.get(pk=documento_id)
        doc.estado = "procesando"
        doc.save(update_fields=['estado'])
    except Documento.DoesNotExist:
        log.error("Documento %s no existe al iniciar la tarea.", documento_id)
        return

    path = doc.archivo.path
    parsed_data = None
    raw_text = ""

    try:
        # --- NUEVA LÓGICA DE SELECCIÓN DE MOTOR ---
        if path.lower().endswith('.xml'):
            log.info("Detectado archivo XML para Documento %s. Usando parser XML.", documento_id)
            parsed_data = extract_data_from_xml(path)
            # El raw_text ya viene dentro del diccionario de datos del XML
            raw_text = parsed_data.get("raw_text", "") if parsed_data else ""

        elif path.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg')):
            log.info("Detectado archivo PDF/Imagen para Documento %s. Usando motor OCR.", documento_id)
            # parse_document devuelve un objeto y el texto plano
            parsed_result_obj, raw_text = parse_document(path)
            
            # Convertimos el objeto a un diccionario para unificar el manejo
            if parsed_result_obj:
                parsed_data = {
                    "tipo_documento": parsed_result_obj.tipo_documento,
                    "folio": parsed_result_obj.folio,
                    "fecha_emision": parsed_result_obj.fecha_emision,
                    "rut_proveedor": parsed_result_obj.rut_proveedor,
                    "proveedor_nombre": parsed_result_obj.proveedor_nombre,
                    "monto_neto": parsed_result_obj.monto_neto,
                    "monto_exento": parsed_result_obj.monto_exento,
                    "iva": parsed_result_obj.iva,
                    "total": parsed_result_obj.total,
                    "iva_tasa": parsed_result_obj.iva_tasa,
                    "fuente_texto": parsed_result_obj.fuente_texto,
                }
        else:
            log.warning("Formato de archivo no soportado para Documento %s: %s", documento_id, path)
            doc.estado = "error_formato"
            doc.save(update_fields=['estado'])
            return
        
        # --- FIN DE LA NUEVA LÓGICA ---

        if not parsed_data:
            raise ValueError("La extracción de datos no devolvió resultados.")

        with transaction.atomic():
            doc_to_update = Documento.objects.get(pk=documento_id)
            
            # Asignar campos desde el diccionario 'parsed_data'
            doc_to_update.tipo_documento = parsed_data.get('tipo_documento', 'desconocido')
            doc_to_update.folio = parsed_data.get('folio')
            doc_to_update.fecha_emision = parsed_data.get('fecha_emision')
            doc_to_update.rut_proveedor = parsed_data.get('rut_proveedor')
            doc_to_update.razon_social_proveedor = parsed_data.get('proveedor_nombre')
            
            # Convertir a Decimal de forma segura
            doc_to_update.monto_neto = Decimal(str(parsed_data.get('monto_neto') or 0))
            doc_to_update.monto_exento = Decimal(str(parsed_data.get('monto_exento') or 0))
            doc_to_update.iva = Decimal(str(parsed_data.get('iva') or 0))
            doc_to_update.total = Decimal(str(parsed_data.get('total') or 0))
            
            iva_tasa = parsed_data.get('iva_tasa')
            doc_to_update.iva_tasa = Decimal(str(iva_tasa)) if iva_tasa is not None else None

            # Guardar campos de auditoría
            doc_to_update.texto_plano = raw_text
            doc_to_update.ocr_fuente = parsed_data.get('fuente_texto', 'desconocido')
            doc_to_update.ocr_engine = "lxml" if doc_to_update.ocr_fuente == "xml" else "Tesseract"
            
            doc_to_update.estado = "procesado"
            doc_to_update.save()

            log.info(
                "Documento %s procesado y GUARDADO CORRECTAMENTE (Fuente: %s, Total: %s)",
                documento_id, doc_to_update.ocr_fuente, doc_to_update.total
            )

            # Lanzar la siguiente tarea en la cadena: la validación con el SII
            check_and_kickoff_sii.apply_async(args=[doc_to_update.id], countdown=1)

    except Exception as e:
        log.exception("Error CRÍTICO al procesar o guardar el documento %s: %s", documento_id, e)
        # Revertir el estado a 'error'
        doc.estado = "error_extraccion"
        doc.save(update_fields=['estado'])