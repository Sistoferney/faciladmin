from django.apps import AppConfig


class PromocionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.promociones'
    verbose_name = 'Promociones'

    def ready(self):
        """
        Importar signals cuando la app esté lista
        """
        import apps.promociones.signals  # noqa
