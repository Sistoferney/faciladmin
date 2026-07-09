# Release phase: Ejecutar migraciones y collectstatic ANTES de iniciar el servidor
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput

# Web process: Solo ejecutar Gunicorn con configuración optimizada
web: gunicorn config.wsgi --log-file - --timeout 120 --workers 2 --bind 0.0.0.0:$PORT
