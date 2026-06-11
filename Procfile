web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn config.wsgi --log-file -
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput
# Script temporal deshabilitado - Ya se creó el superusuario
# && python reset_password_deploy.py
