# Web process: Ejecutar migraciones, collectstatic y Gunicorn
# Railway NO soporta la fase "release" correctamente, por eso todo va en "web"
web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn config.wsgi --log-file - --timeout 120 --workers 2 --bind 0.0.0.0:$PORT
