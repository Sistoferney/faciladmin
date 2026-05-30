"""
Settings package for FacilAdmin
Detecta automáticamente el entorno y carga la configuración correcta
"""
import os

# Detectar entorno (local o production)
ENVIRONMENT = os.environ.get('DJANGO_ENVIRONMENT', 'local')

if ENVIRONMENT == 'production':
    from .production import *
else:
    from .local import *
