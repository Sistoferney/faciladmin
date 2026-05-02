from django.apps import AppConfig


class CitasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.citas'
    verbose_name = 'Citas'

    def ready(self):
        import apps.citas.signals
