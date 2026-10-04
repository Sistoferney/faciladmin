"""
Tareas de Celery para fidelización
RF-28 a RF-32
"""
from celery import shared_task
from django.conf import settings

from apps.notificaciones.models import Notificacion
from apps.notificaciones.services import elegir_canal

from .recuperacion import seguimientos


@shared_task
def sugerir_proximas_citas():
    """
    RF-29, RF-30: Recordar agendar cuando ya pasó la frecuencia del servicio.

    Se ejecuta a diario (11:00). Al cliente que lleva la frecuencia de su
    servicio habitual + 2 días sin volver (y sin citas próximas) se le envía
    UN mensaje para agendar; no se repite hasta que vuelva y se ausente otra vez.
    Si sigue sin volver, a la frecuencia + 50% aparece en "Clientes por
    recuperar" del panel (ver recuperacion.py).
    """
    enviadas = 0
    for seguimiento in seguimientos():
        if not seguimiento.toca_recordatorio:
            continue

        cliente = seguimiento.cliente
        negocio = seguimiento.ultima_cita.negocio
        if not cliente.acepta_promociones:
            continue

        # Una vez por ausencia: ¿ya se le recordó después de su última visita?
        ya_recordado = Notificacion.objects.filter(
            cliente=cliente,
            tipo='sugerencia_cita',
            fecha_creacion__gte=seguimiento.ultima_cita.fecha_hora,
        ).exists()
        if ya_recordado:
            continue

        canal = elegir_canal(cliente)
        if not canal:
            continue

        servicio = seguimiento.servicio.nombre
        enlace = f"{getattr(settings, 'SITE_URL', '').rstrip('/')}/{negocio.slug}/agendar/"
        mensaje = f"""
¡Hola {cliente.nombre}!

Han pasado {seguimiento.dias_sin_venir} días desde tu última cita de {servicio} en {negocio.nombre}.
Para mantener los mejores resultados te recomendamos agendar tu próxima cita.

📅 Agenda aquí: {enlace}

¡Te esperamos!
        """.strip()

        notificacion = Notificacion.objects.create(
            cliente=cliente,
            tipo='sugerencia_cita',
            canal=canal,
            # El push usa la primera parte del asunto como texto
            asunto=f'¿Te agendamos tu próximo {servicio}? - {negocio.nombre}',
            mensaje=mensaje,
        )
        if notificacion.enviar().get('success'):
            enviadas += 1

    return f"Enviados {enviadas} recordatorios para agendar"
