"""
Tareas de Celery para abonos
"""
from celery import shared_task
from django.utils import timezone
from .models import Abono


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
    abonos_vencidos = Abono.objects.filter(
        estado='pendiente',
        fecha_limite__lt=timezone.now()
    )
    abonos_vencidos.update(estado='vencido')

    return f"Verificados {abonos_pendientes.count()} abonos. {abonos_vencidos.count()} marcados como vencidos."
