"""
Cálculo de disponibilidad de la agenda de un negocio
RF-17: Disponibilidad en tiempo real

Única fuente de verdad para el calendario público (APIs) y para validar
en el servidor al agendar o editar una cita.
"""
from datetime import datetime, time, timedelta

from django.utils import timezone

# Intervalo entre horarios ofrecidos
INTERVALO_MINUTOS = 30

# Estados de cita que ocupan la agenda
ESTADOS_QUE_OCUPAN = ['pendiente_abono', 'confirmada']

HORA_APERTURA_DEFECTO = time(9, 0)
HORA_CIERRE_DEFECTO = time(19, 0)


def horario_del_dia(negocio, fecha):
    """
    Retorna (hora_apertura, hora_cierre) del negocio para la fecha,
    o None si ese día está cerrado.
    Usa la configuración por día de la semana si existe; si no, el horario general.
    """
    config_dia = negocio.configuraciones_horario.filter(dia_semana=fecha.weekday()).first()
    if config_dia:
        if not config_dia.esta_abierto:
            return None
        return config_dia.hora_apertura, config_dia.hora_cierre

    return (
        negocio.horario_apertura or HORA_APERTURA_DEFECTO,
        negocio.horario_cierre or HORA_CIERRE_DEFECTO,
    )


def _se_traslapan(inicio_a, fin_a, inicio_b, fin_b):
    return inicio_a < fin_b and inicio_b < fin_a


def horarios_disponibles(negocio, fecha, duracion_minutos, excluir_cita_id=None):
    """
    Lista de horas ('HH:MM') en las que se puede iniciar una cita de la
    duración indicada en la fecha dada.

    Un horario está disponible si:
    - Es futuro
    - La cita empieza y termina dentro del horario de atención del día
    - No se cruza con otra cita activa del negocio
    - No se cruza con un bloqueo de agenda activo

    excluir_cita_id: al editar una cita, para que no choque consigo misma.
    """
    from apps.citas.models import Cita

    horario = horario_del_dia(negocio, fecha)
    if not horario:
        return []
    hora_apertura, hora_cierre = horario

    apertura = timezone.make_aware(datetime.combine(fecha, hora_apertura))
    cierre = timezone.make_aware(datetime.combine(fecha, hora_cierre))
    duracion = timedelta(minutes=duracion_minutos)
    ahora = timezone.now()

    if cierre <= ahora or apertura + duracion > cierre:
        return []

    # Ocupación del día: se consulta una sola vez.
    # Las citas pueden haber empezado el día anterior, por eso el margen.
    citas = Cita.objects.filter(
        negocio=negocio,
        estado__in=ESTADOS_QUE_OCUPAN,
        fecha_hora__lt=cierre,
        fecha_hora__gte=apertura - timedelta(days=1),
    )
    if excluir_cita_id:
        citas = citas.exclude(id=excluir_cita_id)
    ocupados = [
        (c.fecha_hora, c.fecha_hora + timedelta(minutes=c.duracion_minutos))
        for c in citas
    ]
    ocupados += list(
        negocio.bloqueos.filter(
            esta_activo=True,
            fecha_inicio__lt=cierre,
            fecha_fin__gt=apertura,
        ).values_list('fecha_inicio', 'fecha_fin')
    )

    # Primer horario: la apertura redondeada al siguiente intervalo (ej. 9:10 -> 9:30)
    minutos = apertura.hour * 60 + apertura.minute
    desfase = (-minutos) % INTERVALO_MINUTOS
    inicio = apertura + timedelta(minutes=desfase)

    horarios = []
    while inicio + duracion <= cierre:
        fin = inicio + duracion
        if inicio > ahora and not any(
            _se_traslapan(inicio, fin, ini_ocupado, fin_ocupado)
            for ini_ocupado, fin_ocupado in ocupados
        ):
            horarios.append(timezone.localtime(inicio).strftime('%H:%M'))
        inicio += timedelta(minutes=INTERVALO_MINUTOS)

    return horarios


def esta_disponible(negocio, fecha_hora, duracion_minutos, excluir_cita_id=None):
    """
    Verifica que se pueda agendar una cita que inicia en fecha_hora (aware).
    Usa exactamente los mismos horarios que se ofrecen en el calendario.
    """
    local = timezone.localtime(fecha_hora)
    return local.strftime('%H:%M') in horarios_disponibles(
        negocio, local.date(), duracion_minutos, excluir_cita_id
    )
