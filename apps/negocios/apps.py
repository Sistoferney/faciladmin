from django.apps import AppConfig


class NegociosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.negocios'
    verbose_name = 'Negocios'

    def ready(self):
        """
        Importar signals cuando la app esté lista
        Esto permite que los signals se registren automáticamente
        """
        import apps.negocios.signals  # noqa
