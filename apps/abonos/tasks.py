"""
Tareas de Celery para abonos
"""
from celery import shared_task
from django.utils import timezone
from .models import Abono
import logging

logger = logging.getLogger(__name__)


def _avisar_admin_abono_vencido(abono):
    """Notifica por push al dueño que un abono venció sin pagarse"""
    from apps.notificaciones.services import NotificacionService

    cita = abono.cita
    fecha = timezone.localtime(cita.fecha_hora)
    try:
        NotificacionService().enviar_push(
            cliente=cita.cliente,
            titulo='Abono vencido',
            mensaje=(
                f'{cita.cliente.nombre} no pagó el abono de ${abono.monto} '
                f'para {cita.servicio.nombre} el {fecha.strftime("%d/%m/%Y a las %H:%M")}.\n'
                'Revisa Abonos para confirmar el pago o cancelar la cita.'
            ),
            cita=cita,
            enviar_a_admin=True,
        )
    except Exception:
        logger.exception('Error avisando abono vencido %s', abono.id)


@shared_task
def verificar_abonos_pendientes():
    """
    Tarea que verifica abonos pendientes y envía recordatorios
    RF-55, RF-56: Recordatorios de pago
    """
    from apps.notificaciones.tasks import enviar_recordatorio_abono

    # Obtener abonos pendientes
    abonos_pendientes = Abono.objects.filter(
        estado='pendiente',
        fecha_limite__gt=timezone.now()
    )

    for abono in abonos_pendientes:
        dias_para_vencer = abono.dias_para_vencer

        # RF-56: Enviar recordatorios según los días restantes
        if dias_para_vencer == 2:
            # Recordatorio 48h antes
            enviar_recordatorio_abono.delay(abono.id, '48h')
        elif dias_para_vencer == 1:
            # Recordatorio 24h antes
            enviar_recordatorio_abono.delay(abono.id, '24h')

    # Marcar abonos vencidos
    abonos_vencidos = list(Abono.objects.filter(
        estado='pendiente',
        fecha_limite__lt=timezone.now()
    ).select_related('cita__cliente', 'cita__servicio', 'cita__negocio'))
    count_vencidos = Abono.objects.filter(
        id__in=[a.id for a in abonos_vencidos]
    ).update(estado='vencido')

    # La cita NO se cancela automáticamente: el dueño decide si confirma
    # un pago tardío o cancela la cita (desde Abonos > Por revisar).
    # Solo se avisa si la cita aún no ha pasado y sigue esperando el abono:
    # de citas pasadas ya no hay nada que decidir.
    ahora = timezone.now()
    for abono in abonos_vencidos:
        if abono.cita.fecha_hora > ahora and abono.cita.estado == 'pendiente_abono':
            _avisar_admin_abono_vencido(abono)

    return f"Verificados {abonos_pendientes.count()} abonos. {count_vencidos} marcados como vencidos."
