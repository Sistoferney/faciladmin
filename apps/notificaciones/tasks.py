"""
Tareas de Celery para notificaciones
"""
from celery import shared_task
from django.utils import timezone
from datetime import datetime, time, timedelta
from .models import Notificacion
from .services import elegir_canal
from apps.citas.models import Cita
from apps.abonos.models import Abono

import logging

logger = logging.getLogger(__name__)


@shared_task
def enviar_confirmacion_cita(cita_id):
    """
    RF-18: Enviar confirmación de cita
    """
    from apps.citas.models import Cita

    try:
        cita = Cita.objects.get(id=cita_id)
        cliente = cita.cliente
        negocio = cita.negocio

        # Determinar canal preferido
        canal = elegir_canal(cliente)
        resultado = {'success': False, 'error': 'El cliente no tiene canales de notificación disponibles'}
        if canal:
            # Crear mensaje
            mensaje = f"""
¡Hola {cliente.nombre}!

Tu cita ha sido agendada exitosamente:

📅 Fecha: {timezone.localtime(cita.fecha_hora).strftime('%d/%m/%Y')}
🕐 Hora: {timezone.localtime(cita.fecha_hora).strftime('%H:%M')}
✂️ Servicio: {cita.servicio.nombre}
💰 Precio: ${cita.servicio.precio}

📍 {negocio.nombre}
{negocio.direccion}

Gracias por tu preferencia.
            """.strip()

            # Si requiere abono, agregar información
            if cita.requiere_abono:
                info_abono = f"""

⚠️ IMPORTANTE: Esta cita requiere un abono de ${cita.monto_abono}

Datos para transferencia:
🏦 Banco: {negocio.banco}
💳 Cuenta: {negocio.numero_cuenta}
👤 Titular: {negocio.titular_cuenta}

Fecha límite de pago: {timezone.localtime(cita.fecha_limite_abono).strftime('%d/%m/%Y %H:%M')}

Por favor, envía tu comprobante de pago para confirmar tu cita.
                """.strip()
                mensaje += info_abono

            # Crear notificación
            notificacion = Notificacion.objects.create(
                cliente=cliente,
                cita=cita,
                tipo='confirmacion_cita',
                canal=canal,
                asunto=f'Confirmación de cita - {negocio.nombre}',
                mensaje=mensaje
            )

            # Enviar al cliente
            resultado = notificacion.enviar()

        # También enviar notificación push al dueño del negocio
        try:
            from .services import NotificacionService
            service = NotificacionService()

            # Notificación para el admin/dueño
            titulo_admin = "Nueva cita agendada"
            mensaje_admin = f"""
{cliente.nombre} ha agendado una cita:

📅 {timezone.localtime(cita.fecha_hora).strftime('%d/%m/%Y')}
🕐 {timezone.localtime(cita.fecha_hora).strftime('%H:%M')}
✂️ {cita.servicio.nombre}
💰 ${cita.servicio.precio}

📞 Tel: {cliente.telefono}
            """.strip()

            # Enviar push al admin (si está suscrito)
            resultado_admin = service.enviar_push(
                cliente=cliente,
                titulo=titulo_admin,
                mensaje=mensaje_admin,
                cita=cita,
                enviar_a_admin=True  # ← Importante: esto envía también al admin
            )

            if resultado_admin.get('success'):
                logger.info(f"[Notificación Admin] Enviada: {resultado_admin.get('enviados_admin', 0)} notificaciones")

        except Exception:
            # Si falla el envío al admin, no afectar el flujo principal
            logger.exception('Error al notificar al admin la cita %s', cita_id)

        return resultado

    except Cita.DoesNotExist:
        return {'success': False, 'error': 'Cita no encontrada'}


@shared_task
def enviar_recordatorios_citas():
    """
    RF-28: Enviar recordatorios de citas 24h antes

    Se ejecuta diariamente a las 10:00 AM y envía recordatorios a TODAS
    las citas del día siguiente que aún no han recibido recordatorio.
    """
    # Rango: el día de mañana completo en hora de Colombia.
    # (timezone.now() está en UTC: usarlo directo desplazaría el día 5 horas)
    manana = timezone.localdate() + timedelta(days=1)
    inicio_manana = timezone.make_aware(datetime.combine(manana, time.min))
    inicio_pasado_manana = inicio_manana + timedelta(days=1)

    citas = Cita.objects.filter(
        estado='confirmada',
        fecha_hora__gte=inicio_manana,
        fecha_hora__lt=inicio_pasado_manana,
        recordatorio_enviado=False
    ).select_related('cliente', 'negocio', 'servicio')

    enviados = 0
    for cita in citas:
        cliente = cita.cliente
        negocio = cita.negocio

        canal = elegir_canal(cliente)
        if not canal:
            continue

        mensaje = f"""
¡Hola {cliente.nombre}!

Te recordamos tu cita para mañana:

📅 Fecha: {timezone.localtime(cita.fecha_hora).strftime('%d/%m/%Y')}
🕐 Hora: {timezone.localtime(cita.fecha_hora).strftime('%H:%M')}
✂️ Servicio: {cita.servicio.nombre}

📍 {negocio.nombre}
{negocio.direccion}
📞 {negocio.telefono}

Te esperamos.
        """.strip()

        notificacion = Notificacion.objects.create(
            cliente=cliente,
            cita=cita,
            tipo='recordatorio_cita',
            canal=canal,
            asunto=f'Recordatorio de cita - {negocio.nombre}',
            mensaje=mensaje
        )

        resultado = notificacion.enviar()
        if resultado.get('success'):
            cita.recordatorio_enviado = True
            cita.save()
            enviados += 1

    return f"Enviados {enviados} recordatorios de citas"


@shared_task
def enviar_recordatorio_abono(abono_id, momento):
    """
    RF-56: Enviar recordatorios de pago de abono
    """
    try:
        abono = Abono.objects.get(id=abono_id)
        cita = abono.cita
        cliente = cita.cliente
        negocio = cita.negocio

        # Determinar canal
        canal = elegir_canal(cliente)
        if not canal:
            return

        mensaje = f"""
¡Hola {cliente.nombre}!

Recordatorio de pago de abono para tu cita:

📅 Fecha de cita: {timezone.localtime(cita.fecha_hora).strftime('%d/%m/%Y %H:%M')}
✂️ Servicio: {cita.servicio.nombre}
💰 Monto de abono: ${abono.monto}

⏰ Fecha límite: {timezone.localtime(abono.fecha_limite).strftime('%d/%m/%Y %H:%M')}

Datos para transferencia:
🏦 Banco: {negocio.banco}
💳 Cuenta: {negocio.numero_cuenta}
👤 Titular: {negocio.titular_cuenta}

Por favor, envía tu comprobante de pago lo antes posible.

{negocio.nombre}
        """.strip()

        notificacion = Notificacion.objects.create(
            cliente=cliente,
            cita=cita,
            tipo='recordatorio_abono',
            canal=canal,
            asunto=f'Recordatorio de pago - {negocio.nombre}',
            mensaje=mensaje
        )

        return notificacion.enviar()

    except Abono.DoesNotExist:
        return {'success': False, 'error': 'Abono no encontrado'}


@shared_task
def enviar_notificacion_confirmacion_abono(cita_id):
    """
    RF-57: Notificar confirmación de abono
    """
    try:
        cita = Cita.objects.get(id=cita_id)
        cliente = cita.cliente
        negocio = cita.negocio

        # Determinar canal
        canal = elegir_canal(cliente)
        if not canal:
            return

        mensaje = f"""
¡Hola {cliente.nombre}!

✅ Tu pago ha sido confirmado. Tu cita está asegurada:

📅 Fecha: {timezone.localtime(cita.fecha_hora).strftime('%d/%m/%Y')}
🕐 Hora: {timezone.localtime(cita.fecha_hora).strftime('%H:%M')}
✂️ Servicio: {cita.servicio.nombre}

📍 {negocio.nombre}
{negocio.direccion}

¡Te esperamos!
        """.strip()

        notificacion = Notificacion.objects.create(
            cliente=cliente,
            cita=cita,
            tipo='confirmacion_abono',
            canal=canal,
            asunto=f'Pago confirmado - {negocio.nombre}',
            mensaje=mensaje
        )

        return notificacion.enviar()

    except Cita.DoesNotExist:
        return {'success': False, 'error': 'Cita no encontrada'}


# Cambios hechos por el dueño desde el panel que se avisan al cliente.
# (La confirmación de abono usa enviar_notificacion_confirmacion_abono)
EVENTOS_CITA = {
    'confirmada': {
        'tipo': 'confirmacion_cita',
        'asunto': 'Cita confirmada',
        'texto': '✅ Tu cita está confirmada. ¡Te esperamos!',
    },
    'cancelada': {
        'tipo': 'cancelacion',
        'asunto': 'Cita cancelada',
        'texto': '❌ Tu cita fue cancelada por {negocio}.',
    },
    'abono_rechazado': {
        'tipo': 'abono_rechazado',
        'asunto': 'No pudimos validar tu pago',
        'texto': '⚠️ No pudimos validar el pago del abono de tu cita.',
    },
}


@shared_task
def notificar_cambio_cita(cita_id, evento, motivo=''):
    """
    Avisa al cliente un cambio en su cita hecho por el dueño desde el panel:
    'confirmada', 'cancelada' o 'abono_rechazado'.
    """
    config = EVENTOS_CITA[evento]
    try:
        cita = Cita.objects.select_related('cliente', 'negocio', 'servicio').get(id=cita_id)
    except Cita.DoesNotExist:
        return {'success': False, 'error': 'Cita no encontrada'}

    cliente = cita.cliente
    negocio = cita.negocio
    canal = elegir_canal(cliente)
    if not canal:
        return {'success': False, 'error': 'El cliente no tiene canales de notificación disponibles'}

    fecha = timezone.localtime(cita.fecha_hora)
    mensaje = f"""
¡Hola {cliente.nombre}!

{config['texto'].format(negocio=negocio.nombre)}

📅 Fecha: {fecha.strftime('%d/%m/%Y')}
🕐 Hora: {fecha.strftime('%H:%M')}
✂️ Servicio: {cita.servicio.nombre}

📍 {negocio.nombre}
    """.strip()

    if motivo:
        mensaje += f"\n\n💬 Motivo: {motivo}"

    notificacion = Notificacion.objects.create(
        cliente=cliente,
        cita=cita,
        tipo=config['tipo'],
        canal=canal,
        asunto=f"{config['asunto']} - {negocio.nombre}",
        mensaje=mensaje
    )
    return notificacion.enviar()


def programar_notificacion(tarea, *args):
    """
    Ejecuta la tarea al confirmarse la transacción: en segundo plano si hay
    worker de Celery, o en el momento si no hay Redis (modo EAGER).
    Un fallo al notificar nunca debe romper la acción del dueño.
    """
    from django.conf import settings
    from django.db import transaction

    def ejecutar():
        try:
            if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
                tarea(*args)
            else:
                tarea.delay(*args)
        except Exception:
            logger.exception('Error enviando notificación %s%s', tarea.name, args)

    transaction.on_commit(ejecutar)
