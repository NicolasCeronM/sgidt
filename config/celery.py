# config/celery.py
import os
from celery import Celery
from celery.schedules import crontab

# Establece el módulo de configuración de Django para el proceso de Celery.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE", "config.settings"))

app = Celery("config")

# Lee la configuración de Celery desde tu archivo settings.py.
# El namespace 'CELERY' significa que todas las configuraciones de Celery
# deben empezar con CELERY_ (ej: CELERY_BROKER_URL).
app.config_from_object("django.conf:settings", namespace="CELERY")

# Descubre automáticamente las tareas en todos los archivos tasks.py de tus apps.
app.autodiscover_tasks()

# --- NUEVO: Configuración de Tareas Periódicas (Celery Beat) ---
# Aquí es donde se define la ejecución recurrente de tareas.
app.conf.beat_schedule = {
    # 1. TAREA DE CORREOS: Se ejecutará cada 2 minutos (ej: 14:00, 14:02, 14:04...)
    'check-emails-frecuente': {
        'task': 'correo.check_all_emails',
        'schedule': crontab(minute='*/2'), 
        'options': {'queue': 'correos'},
    },

    # 2. TAREA DE ALERTAS: Se ejecutará cada 5 minutos (ej: 14:00, 14:05, 14:10...)
    # Esto te asegura que en máximo 5 min recibirás el correo de prueba.
    'alerta-diaria-test': {
        'task': 'documentos.check_daily_alerts',
        'schedule': crontab(minute='*/5'), 
        'options': {'queue': 'default'},
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """ Tarea de depuración para verificar que Celery funciona. """
    print(f'Request: {self.request!r}')