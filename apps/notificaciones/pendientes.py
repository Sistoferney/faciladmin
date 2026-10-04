"""
Bandeja de pendientes del dueño: crear y resolver tareas.

Reglas:
- Nueva cita            -> 'cita_nueva' (se resuelve al actuar sobre la cita o marcarla revisada)
- Cita con abono        -> 'abono' (uno por cita; comprobante / vencido / rechazo lo actualizan)
                           se resuelve al confirmar o exonerar el pago
- Cliente modifica cita -> 'cita_modificada' (el dueño marca "Entendido")
- Cliente cancela cita  -> 'cita_cancelada'  (el dueño marca "Entendido")
- Cita cancelada, completada o no asistió -> se resuelven los demás pendientes de la cita
"""
from django.utils import timezone

ESTADOS_CITA_CERRADA = ('cancelada', 'completada', 'no_asistio')


def abrir(cita, tipo, detalle='', novedad=True):
    """
    Crea el pendiente, o actualiza el abierto del mismo tipo para esa cita.
    novedad=True: lo sube en la bandeja y el panel lo detecta como novedad
    (notificación local). False para cambios que hizo el propio dueño.
    """
    from .models import Pendiente

    pendiente = Pendiente.objects.filter(cita=cita, tipo=tipo, resuelto=False).first()
    if pendiente:
        if novedad:
            if detalle:
                pendiente.detalle = detalle
            pendiente.save()  # actualiza actualizado_en
        elif detalle:
            # update() no toca actualizado_en: no aparece como novedad
            Pendiente.objects.filter(pk=pendiente.pk).update(detalle=detalle)
            pendiente.detalle = detalle
        return pendiente
    return Pendiente.objects.create(negocio_id=cita.negocio_id, cita=cita, tipo=tipo, detalle=detalle)


def resolver(cita, tipos=None, excepto=()):
    """Marca como resueltos los pendientes abiertos de la cita (opcionalmente solo algunos tipos)"""
    from .models import Pendiente

    pendientes = Pendiente.objects.filter(cita=cita, resuelto=False)
    if tipos:
        pendientes = pendientes.filter(tipo__in=tipos)
    if excepto:
        pendientes = pendientes.exclude(tipo__in=excepto)
    ahora = timezone.now()
    return pendientes.update(resuelto=True, resuelto_en=ahora, actualizado_en=ahora)
