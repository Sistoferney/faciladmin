from django.apps import AppConfig


class NotificacionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notificaciones'
    verbose_name = 'Notificaciones'

    def ready(self):
        # Bandeja de pendientes del dueño (crear/resolver al cambiar citas y abonos)
        from . import signals  # noqa: F401
