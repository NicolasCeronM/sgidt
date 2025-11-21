from celery import shared_task
import logging
# CORRECCIÓN: Importar desde 'alerts' (nombre del archivo) y la función 'check_and_send_alerts'
from apps.documentos.services.alerts import check_and_send_alerts 

logger = logging.getLogger(__name__)

@shared_task(name="documentos.check_daily_alerts")
def task_check_daily_alerts():
    """
    Tarea programada para revisar alertas de documentos y notificar.
    """
    logger.info("TAREA: Iniciando chequeo diario de alertas...")
    try:
        check_and_send_alerts()
        logger.info("TAREA: Chequeo de alertas finalizado correctamente.")
    except Exception as e:
        logger.error(f"TAREA ERROR: Falló el chequeo de alertas: {e}", exc_info=True)