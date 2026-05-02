"""
Signals para el modelo Cita
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Cita
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Cita)
def cita_creada(sender, instance, created, **kwargs):
    """
    Signal que se ejecuta cuando se crea una nueva cita
    RF-18: Enviar confirmación de cita
    """
    if created:
        try:
            # Enviar confirmación al cliente
            from apps.notificaciones.tasks import enviar_confirmacion_cita

            # Si Celery está en modo EAGER o hay error de conexión, ejecutar directamente
            if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
                enviar_confirmacion_cita(instance.id)
            else:
                enviar_confirmacion_cita.delay(instance.id)
        except Exception as e:
            # Si falla (por ejemplo, Redis no disponible), solo registrar el error
            logger.warning(f"No se pudo enviar confirmación de cita: {e}")


@receiver(post_save, sender=Cita)
def cita_confirmada(sender, instance, **kwargs):
    """
    Signal cuando la cita es confirmada por el admin
    RF-57: Notificar confirmación
    """
    if instance.confirmada_por_admin and not instance.confirmacion_enviada:
        try:
            # Enviar notificación de confirmación
            from apps.notificaciones.tasks import enviar_notificacion_confirmacion_abono

            # Si Celery está en modo EAGER o hay error de conexión, ejecutar directamente
            if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
                enviar_notificacion_confirmacion_abono(instance.id)
            else:
                enviar_notificacion_confirmacion_abono.delay(instance.id)

            instance.confirmacion_enviada = True
            instance.save(update_fields=['confirmacion_enviada'])
        except Exception as e:
            # Si falla, solo registrar el error
            logger.warning(f"No se pudo enviar notificación de confirmación: {e}")
