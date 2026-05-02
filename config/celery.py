"""
Celery configuration for FacilAdmin project.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('faciladmin')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Configuración de tareas periódicas
app.conf.beat_schedule = {
    'enviar-recordatorios-24h': {
        'task': 'apps.notificaciones.tasks.enviar_recordatorios_citas',
        'schedule': crontab(hour=10, minute=0),  # Todos los días a las 10:00 AM
    },
    'verificar-abonos-pendientes': {
        'task': 'apps.abonos.tasks.verificar_abonos_pendientes',
        'schedule': crontab(hour=9, minute=0),  # Todos los días a las 9:00 AM
    },
    'identificar-clientes-inactivos': {
        'task': 'apps.fidelizacion.tasks.identificar_clientes_inactivos',
        'schedule': crontab(day_of_week=1, hour=8, minute=0),  # Todos los lunes a las 8:00 AM
    },
    'sugerir-proximas-citas': {
        'task': 'apps.fidelizacion.tasks.sugerir_proximas_citas',
        'schedule': crontab(hour=11, minute=0),  # Todos los días a las 11:00 AM
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
