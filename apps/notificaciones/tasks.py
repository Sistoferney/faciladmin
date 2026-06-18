"""
Tareas de Celery para notificaciones
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Notificacion
from apps.citas.models import Cita
from apps.abonos.models import Abono


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
        if cliente.acepta_whatsapp:
            canal = 'whatsapp'
        elif cliente.acepta_sms:
            canal = 'sms'
        elif cliente.acepta_email and cliente.email:
            canal = 'email'
        else:
            return

        # Crear mensaje
        mensaje = f"""
¡Hola {cliente.nombre}!

Tu cita ha sido agendada exitosamente:

📅 Fecha: {cita.fecha_hora.strftime('%d/%m/%Y')}
🕐 Hora: {cita.fecha_hora.strftime('%H:%M')}
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
📝 CLABE: {negocio.clabe}
👤 Titular: {negocio.titular_cuenta}

Fecha límite de pago: {cita.fecha_limite_abono.strftime('%d/%m/%Y %H:%M')}

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

        # Enviar
        resultado = notificacion.enviar()
        return resultado

    except Cita.DoesNotExist:
        return {'success': False, 'error': 'Cita no encontrada'}


@shared_task
def enviar_recordatorios_citas():
    """
    RF-28: Enviar recordatorios de citas 24h antes
    """
    manana = timezone.now() + timedelta(hours=24)
    inicio_ventana = manana - timedelta(hours=1)
    fin_ventana = manana + timedelta(hours=1)

    citas = Cita.objects.filter(
        estado='confirmada',
        fecha_hora__gte=inicio_ventana,
        fecha_hora__lte=fin_ventana,
        recordatorio_enviado=False
    )

    enviados = 0
    for cita in citas:
        cliente = cita.cliente
        negocio = cita.negocio

        # Determinar canal (prioridad: Push > WhatsApp > SMS > Email)
        # Push es GRATIS y no requiere configuración de Twilio
        canal = 'push'  # Intentar push primero (gratis, funciona con PWA instalada)

        # Fallback si push falla
        if not canal:
            if cliente.acepta_whatsapp:
                canal = 'whatsapp'
            elif cliente.acepta_sms:
                canal = 'sms'
            elif cliente.acepta_email and cliente.email:
                canal = 'email'
            else:
                continue

        mensaje = f"""
¡Hola {cliente.nombre}!

Te recordamos tu cita para mañana:

📅 Fecha: {cita.fecha_hora.strftime('%d/%m/%Y')}
🕐 Hora: {cita.fecha_hora.strftime('%H:%M')}
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
        if cliente.acepta_whatsapp:
            canal = 'whatsapp'
        elif cliente.acepta_sms:
            canal = 'sms'
        elif cliente.acepta_email and cliente.email:
            canal = 'email'
        else:
            return

        mensaje = f"""
¡Hola {cliente.nombre}!

Recordatorio de pago de abono para tu cita:

📅 Fecha de cita: {cita.fecha_hora.strftime('%d/%m/%Y %H:%M')}
✂️ Servicio: {cita.servicio.nombre}
💰 Monto de abono: ${abono.monto}

⏰ Fecha límite: {abono.fecha_limite.strftime('%d/%m/%Y %H:%M')}

Datos para transferencia:
🏦 Banco: {negocio.banco}
💳 Cuenta: {negocio.numero_cuenta}
📝 CLABE: {negocio.clabe}
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
        if cliente.acepta_whatsapp:
            canal = 'whatsapp'
        elif cliente.acepta_sms:
            canal = 'sms'
        elif cliente.acepta_email and cliente.email:
            canal = 'email'
        else:
            return

        mensaje = f"""
¡Hola {cliente.nombre}!

✅ Tu pago ha sido confirmado. Tu cita está asegurada:

📅 Fecha: {cita.fecha_hora.strftime('%d/%m/%Y')}
🕐 Hora: {cita.fecha_hora.strftime('%H:%M')}
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
