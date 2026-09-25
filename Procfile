# Web process: Ejecutar migraciones, collectstatic y Gunicorn
# Railway NO soporta la fase "release" correctamente, por eso todo va en "web"
web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn config.wsgi --log-file - --timeout 120 --workers 2 --bind 0.0.0.0:$PORT

# Celery worker: Procesa tareas asíncronas (requiere Redis)
# Para habilitar en Railway: crear nuevo servicio y seleccionar "worker" como proceso
worker: celery -A config worker --loglevel=info --concurrency=2

# Celery beat: Programa tareas periódicas como recordatorios (requiere Redis)
# Para habilitar en Railway: crear nuevo servicio y seleccionar "beat" como proceso
# IMPORTANTE: Solo debe haber UNA instancia de beat corriendo
beat: celery -A config beat --loglevel=info
