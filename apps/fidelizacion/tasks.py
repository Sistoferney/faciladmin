"""
Tareas de Celery para fidelización
RF-28 a RF-32
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from apps.clientes.models import Cliente
from apps.citas.models import Cita
from apps.notificaciones.models import Notificacion


@shared_task
def sugerir_proximas_citas():
    """
    RF-29, RF-30: Sugerir próximas citas basado en frecuencia del servicio
    """
    # Obtener citas completadas
    citas_completadas = Cita.objects.filter(
        estado='completada',
        servicio__frecuencia_dias__isnull=False
    ).select_related('cliente', 'servicio', 'negocio')

    sugerencias_enviadas = 0

    for cita in citas_completadas:
        # Calcular fecha sugerida para próxima cita
        dias_desde_cita = (timezone.now() - cita.fecha_hora).days
        frecuencia = cita.servicio.frecuencia_dias

        # Si está cerca de la fecha sugerida (5 días antes)
        if dias_desde_cita >= (frecuencia - 5) and dias_desde_cita <= frecuencia:
            # Verificar que no tenga otra cita ya agendada
            tiene_cita_futura = Cita.objects.filter(
                cliente=cita.cliente,
                servicio=cita.servicio,
                fecha_hora__gte=timezone.now(),
                estado__in=['pendiente_abono', 'confirmada']
            ).exists()

            if tiene_cita_futura:
                continue

            # Verificar que no se haya enviado sugerencia recientemente
            sugerencia_reciente = Notificacion.objects.filter(
                cliente=cita.cliente,
                tipo='sugerencia_cita',
                fecha_creacion__gte=timezone.now() - timedelta(days=30)
            ).exists()

            if sugerencia_reciente:
                continue

            # Determinar canal
            cliente = cita.cliente
            negocio = cita.negocio

            if not cliente.acepta_promociones:
                continue

            if cliente.acepta_whatsapp:
                canal = 'whatsapp'
            elif cliente.acepta_sms:
                canal = 'sms'
            elif cliente.acepta_email and cliente.email:
                canal = 'email'
            else:
                continue

            # Crear mensaje
            mensaje = f"""
¡Hola {cliente.nombre}!

Es momento de agendar tu próxima cita de {cita.servicio.nombre}.

Según tu última visita, te recomendamos agendar una nueva cita pronto para mantener los mejores resultados.

💰 Precio: ${cita.servicio.precio}
⏱️ Duración: {cita.servicio.duracion_minutos} minutos

📍 {negocio.nombre}
📞 {negocio.telefono}
🌐 {negocio.url_publica}

¡Agenda tu cita ahora!
            """.strip()

            # Crear notificación
            notificacion = Notificacion.objects.create(
                cliente=cliente,
                tipo='sugerencia_cita',
                canal=canal,
                asunto=f'Es momento de tu próxima cita - {negocio.nombre}',
                mensaje=mensaje
            )

            resultado = notificacion.enviar()
            if resultado.get('success'):
                sugerencias_enviadas += 1

    return f"Enviadas {sugerencias_enviadas} sugerencias de próximas citas"


@shared_task
def identificar_clientes_inactivos():
    """
    RF-31: Identificar clientes inactivos (sin citas en 90+ días)
    RF-32: Enviar promociones de reactivación
    """
    fecha_limite = timezone.now() - timedelta(days=90)

    clientes_inactivos = Cliente.objects.filter(
        ultima_visita__lt=fecha_limite,
        esta_activo=True
    ).exclude(tipo_cliente='inactivo')

    # Marcar como inactivos
    for cliente in clientes_inactivos:
        cliente.tipo_cliente = 'inactivo'
        cliente.save()

    return f"Identificados {clientes_inactivos.count()} clientes inactivos"


@shared_task
def enviar_campana_reactivacion():
    """
    RF-32: Enviar promociones a clientes inactivos
    """
    clientes_inactivos = Cliente.objects.filter(
        tipo_cliente='inactivo',
        esta_activo=True,
        acepta_promociones=True
    )

    enviados = 0

    for cliente in clientes_inactivos:
        negocio = cliente.negocio

        # Verificar que no se haya enviado reactivación recientemente
        reactivacion_reciente = Notificacion.objects.filter(
            cliente=cliente,
            tipo='reactivacion',
            fecha_creacion__gte=timezone.now() - timedelta(days=60)
        ).exists()

        if reactivacion_reciente:
            continue

        # Determinar canal
        if cliente.acepta_whatsapp:
            canal = 'whatsapp'
        elif cliente.acepta_sms:
            canal = 'sms'
        elif cliente.acepta_email and cliente.email:
            canal = 'email'
        else:
            continue

        # Crear mensaje
        mensaje = f"""
¡Hola {cliente.nombre}!

¡Te extrañamos en {negocio.nombre}!

Han pasado varios meses desde tu última visita. Nos encantaría verte de nuevo.

🎁 Tenemos una promoción especial para ti.

Agenda tu cita y recibe un descuento especial.

📍 {negocio.nombre}
📞 {negocio.telefono}
🌐 {negocio.url_publica}

¡Esperamos verte pronto!
        """.strip()

        notificacion = Notificacion.objects.create(
            cliente=cliente,
            tipo='reactivacion',
            canal=canal,
            asunto=f'¡Te extrañamos! - {negocio.nombre}',
            mensaje=mensaje
        )

        resultado = notificacion.enviar()
        if resultado.get('success'):
            enviados += 1

    return f"Enviadas {enviados} campañas de reactivación"
