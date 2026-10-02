# Config package

# Cargar la app de Celery al iniciar Django (también en el servidor web), para
# que las tareas (@shared_task) usen su configuración: broker = REDIS_URL.
# Sin esto, .delay() desde el web usaba la configuración por defecto de Celery
# (localhost) y fallaba con "Connection refused".
from .celery import app as celery_app

__all__ = ('celery_app',)
