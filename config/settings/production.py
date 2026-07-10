"""
Configuración para producción (Railway, Render, etc.)
"""
from .base import *
import dj_database_url

# SECURITY
DEBUG = config('DEBUG', default=False, cast=bool)
SECRET_KEY = config('SECRET_KEY')  # Obligatorio en producción

# Hosts permitidos - Railway proporciona RAILWAY_STATIC_URL
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='.railway.app,.up.railway.app'
).split(',')

# También permitir el dominio custom si existe
RAILWAY_STATIC_URL = config('RAILWAY_STATIC_URL', default='')
if RAILWAY_STATIC_URL:
    domain = RAILWAY_STATIC_URL.replace('https://', '').replace('http://', '')
    if domain not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(domain)

# Database - Railway proporciona DATABASE_URL
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Static files - Usar WhiteNoise para servir archivos estáticos
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files - Cloudinary para almacenamiento permanente
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Cloudinary Configuration
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config('CLOUDINARY_CLOUD_NAME', default=''),
    'API_KEY': config('CLOUDINARY_API_KEY', default=''),
    'API_SECRET': config('CLOUDINARY_API_SECRET', default=''),
    # Configuración para evitar duplicados
    'INVALIDATE': True,  # Invalidar cache del CDN al actualizar
}

# Usar Cloudinary para archivos media en producción
if CLOUDINARY_STORAGE['CLOUD_NAME']:
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    CLOUDINARY_URL = f"cloudinary://{CLOUDINARY_STORAGE['API_KEY']}:{CLOUDINARY_STORAGE['API_SECRET']}@{CLOUDINARY_STORAGE['CLOUD_NAME']}"

# Security Settings
# Railway maneja SSL en su proxy, no necesitamos redirigir desde Django
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)

# Confiar en el proxy de Railway para headers HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CORS - Más restrictivo en producción
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default=''
).split(',') if config('CORS_ALLOWED_ORIGINS', default='') else []

# Email - Usar Resend (HTTPS) en producción en lugar de SMTP
# Resend funciona en Railway sin plan Pro porque usa puerto 443 (HTTPS)
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='apps.core.email_backends.resend_backend.ResendEmailBackend'
)

# Resend API Configuration
RESEND_API_KEY = config('RESEND_API_KEY', default='')

# Celery - Usar Redis en producción
USE_CELERY_EAGER = config('USE_CELERY_EAGER', default=False, cast=bool)

if not USE_CELERY_EAGER:
    # Railway proporciona REDIS_URL automáticamente si agregas Redis
    CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')
else:
    # Modo eager para producción sin Redis (no recomendado pero funcional)
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    CELERY_BROKER_URL = 'memory://'
    CELERY_RESULT_BACKEND = 'cache+memory://'

# Site URL - Railway proporciona RAILWAY_STATIC_URL
SITE_URL = config('SITE_URL', default=RAILWAY_STATIC_URL if RAILWAY_STATIC_URL else 'https://faciladmin.up.railway.app')

# Logging para producción
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# Admin customization
ADMIN_URL = config('ADMIN_URL', default='admin/')
