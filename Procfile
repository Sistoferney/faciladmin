web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && python reset_password_deploy.py && gunicorn config.wsgi --log-file -
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput && python reset_password_deploy.py
