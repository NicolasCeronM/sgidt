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
    # Nombre descriptivo de la tarea programada
    'check-emails-every-15-minutes': {
        # Ruta a la tarea que quieres ejecutar.
        # 'apps.correo.tasks.check_all_emails' es otra forma válida de escribirlo.
        'task': 'correo.check_all_emails',
        
        # Frecuencia de ejecución en segundos. 900 segundos = 15 minutos.
        'schedule': 600.0,
        
        # (Opcional) Argumentos para la tarea, si los necesitara.
        # 'args': (16, 16),
    },
    # --- Puedes añadir más tareas programadas aquí ---
    # 'nombre-de-otra-tarea': {
    #     'task': 'ruta.a.otra.tarea',
    #     # Ejemplo de ejecución cada día a las 7:30 AM
    #     'schedule': crontab(hour=7, minute=30),
    # }
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """ Tarea de depuración para verificar que Celery funciona. """
    print(f'Request: {self.request!r}')