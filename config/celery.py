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
    'check-emails-cada-5-min': {
        'task': 'correo.check_all_emails',   # <- TU tarea real
        'schedule': 300.0,                   # 5 minutos (corrige el comentario)
        'options': {'queue': 'correos'},     # opcional: rutar a cola "correos"
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """ Tarea de depuración para verificar que Celery funciona. """
    print(f'Request: {self.request!r}')