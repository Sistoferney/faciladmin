"""
Señales que mantienen al día la bandeja de pendientes del dueño
(ver pendientes.py para las reglas).
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.abonos.models import Abono
from apps.citas.models import Cita

from . import pendientes


@receiver(post_save, sender=Cita, dispatch_uid='pendientes_cita')
def pendientes_por_cita(sender, instance, created, **kwargs):
    if created:
        pendientes.abrir(instance, 'cita_nueva')
    elif instance.estado in pendientes.ESTADOS_CITA_CERRADA:
        # Cancelada, completada o no asistió: ya no hay nada que revisar ni cobrar.
        # El aviso de "cancelada por el cliente" se mantiene hasta que el dueño lo vea.
        pendientes.resolver(instance, excepto=('cita_cancelada',))


@receiver(post_save, sender=Abono, dispatch_uid='pendientes_abono')
def pendientes_por_abono(sender, instance, created, **kwargs):
    if created:
        pendientes.abrir(instance.cita, 'abono', 'Esperando pago')
    elif instance.estado in ('confirmado', 'exonerado'):
        # Pago resuelto: también se da por revisada la cita
        pendientes.resolver(instance.cita, tipos=['abono', 'cita_nueva'])
    elif instance.estado == 'rechazado':
        # Lo hizo el dueño: se actualiza el texto sin avisarle como novedad
        pendientes.abrir(instance.cita, 'abono', 'Pago rechazado: esperando nuevo comprobante', novedad=False)
