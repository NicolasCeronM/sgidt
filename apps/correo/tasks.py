# apps/correo/tasks.py

from celery import shared_task
import logging
from apps.empresas.models import Empresa
# Asegúrate de que los nombres de las funciones importadas coincidan con tu services.py
from .services import get_unread_email_ids, process_email_batch_from_ids

logger = logging.getLogger(__name__)

@shared_task(name="correo.check_all_emails")
def check_all_emails():
    """
    Tarea periódica: busca empresas con correo y lanza el inicio del proceso.
    """
    empresas_con_correo = Empresa.objects.filter(
        email_host__isnull=False, email_user__isnull=False
    ).exclude(email_host='')
    
    for empresa in empresas_con_correo:
        start_email_processing_chain.delay(empresa.id)

@shared_task(name="correo.start_email_processing_chain")
def start_email_processing_chain(empresa_id: int):
    """
    Tarea INICIADORA: Obtiene la lista COMPLETA de correos no leídos y
    lanza la PRIMERA tarea de la cadena de procesamiento.
    """
    try:
        empresa = Empresa.objects.get(pk=empresa_id)
        # Obtenemos todos los IDs de una vez
        email_ids_bytes = get_unread_email_ids(empresa)

        if not email_ids_bytes:
            return {"ok": True, "detail": "no_new_emails", "empresa_rut": empresa.rut}

        total_emails = len(email_ids_bytes)
        logger.info(f"Empresa {empresa.rut}: {total_emails} correos encontrados. Iniciando cadena de procesamiento.")
        
        # Convertimos a string para que sea serializable por Celery
        email_ids_str = [eid.decode('utf-8') for eid in email_ids_bytes]
        
        # Lanzamos solo la PRIMERA tarea de la cadena
        process_email_chain_batch.delay(empresa_id, email_ids_str)
            
        return {"ok": True, "empresa_rut": empresa.rut, "emails_found": total_emails}
    except Empresa.DoesNotExist:
        return {"ok": False, "error": "empresa_not_found"}
    except Exception as e:
        logger.error(f"Fallo la tarea iniciadora para empresa {empresa_id}: {e}", exc_info=True)
        return {"ok": False, "error": str(e)}

@shared_task(name="correo.process_email_chain_batch", time_limit=300, soft_time_limit=240)
def process_email_chain_batch(empresa_id: int, remaining_ids_str: list[str]):
    """
    Tarea TRABAJADORA y RECURSIVA:
    1. Toma un lote de la lista de IDs restantes.
    2. Procesa ese lote.
    3. Si quedan más IDs, se llama a sí misma con el resto de la lista.
    """
    try:
        empresa = Empresa.objects.get(pk=empresa_id)
        
        batch_size = 100
        # Tomamos el primer lote de la lista
        current_batch_str = remaining_ids_str[:batch_size]
        # El resto de la lista para la siguiente tarea
        next_batch_str = remaining_ids_str[batch_size:]

        logger.info(f"Procesando lote de {len(current_batch_str)} correos para {empresa.rut}. Quedan {len(next_batch_str)}.")
        
        # Procesamos el lote actual
        current_batch_bytes = [eid.encode('utf-8') for eid in current_batch_str]
        process_email_batch_from_ids(empresa, current_batch_bytes)

        # Si quedan correos, lanzamos la siguiente tarea en la cadena
        if next_batch_str:
            process_email_chain_batch.delay(empresa_id, next_batch_str)
            
        return {"ok": True, "processed_count": len(current_batch_str)}
    except Exception as e:
        logger.error(f"Fallo un lote en la cadena para empresa {empresa_id}: {e}", exc_info=True)
        return {"ok": False, "error": str(e)}   