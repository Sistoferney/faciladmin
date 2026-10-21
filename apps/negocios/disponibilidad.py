"""
Cálculo de disponibilidad de la agenda de un negocio
RF-17: Disponibilidad en tiempo real

Única fuente de verdad para el calendario público (APIs) y para validar
en el servidor al agendar o editar una cita.

Dos modos:
- Una sola agenda (0 o 1 especialista activo): como siempre, el negocio
  atiende una cita a la vez.
- Varios especialistas (2 o más activos): cada uno tiene su agenda. Un
  horario está libre para un especialista si está dentro de su horario y no
  se cruza con sus citas ni con sus bloqueos (ni con los del negocio).
  Las citas sin especialista (anteriores a tener varios) ocupan a todos,
  para no agendar dos citas encima; el dueño puede asignarlas desde la agenda.
"""
from datetime import datetime, time, timedelta

from django.utils import timezone

# Intervalo entre horarios ofrecidos
INTERVALO_MINUTOS = 30

# Estados de cita que ocupan la agenda
ESTADOS_QUE_OCUPAN = ['pendiente_abono', 'confirmada']

HORA_APERTURA_DEFECTO = time(9, 0)
HORA_CIERRE_DEFECTO = time(19, 0)

# Desde cuántos especialistas activos el cliente elige con quién
MINIMO_ESPECIALISTAS = 2


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


def especialistas_activos(negocio):
    return list(negocio.especialistas.filter(esta_activo=True).select_related('negocio').prefetch_related('servicios', 'horarios'))


def tiene_varios_especialistas(negocio):
    """True si el cliente debe elegir especialista (2 o más activos)"""
    return negocio.especialistas.filter(esta_activo=True).count() >= MINIMO_ESPECIALISTAS


def especialistas_para(negocio, servicio=None):
    """Especialistas activos que hacen el servicio (todos si no se indica)"""
    return [e for e in especialistas_activos(negocio) if servicio is None or e.hace_servicio(servicio)]


def horario_especialista(especialista, fecha):
    """(desde, hasta) del especialista ese día, o None si no trabaja"""
    if especialista.usa_horario_negocio:
        return horario_del_dia(especialista.negocio, fecha)
    for horario in especialista.horarios.all():
        if horario.dia_semana == fecha.weekday():
            return (horario.hora_apertura, horario.hora_cierre) if horario.esta_abierto else None
    return None  # horario propio sin ese día: no trabaja


def _se_traslapan(inicio_a, fin_a, inicio_b, fin_b):
    return inicio_a < fin_b and inicio_b < fin_a


def _ocupacion_del_dia(negocio, fecha, excluir_cita_id=None):
    """
    Citas activas y bloqueos que pueden cruzarse con el día, como
    (inicio, fin, especialista_id). Se consulta una sola vez por día.
    Las citas pueden haber empezado el día anterior, por eso el margen.
    """
    from apps.citas.models import Cita

    inicio_dia = timezone.make_aware(datetime.combine(fecha, time.min))
    fin_dia = inicio_dia + timedelta(days=1)

    citas = Cita.objects.filter(
        negocio=negocio,
        estado__in=ESTADOS_QUE_OCUPAN,
        fecha_hora__lt=fin_dia,
        fecha_hora__gte=inicio_dia - timedelta(days=1),
    )
    if excluir_cita_id:
        citas = citas.exclude(id=excluir_cita_id)
    ocupacion_citas = [
        (c.fecha_hora, c.fecha_hora + timedelta(minutes=c.duracion_minutos), c.especialista_id)
        for c in citas.only('fecha_hora', 'duracion_minutos', 'especialista_id')
    ]
    ocupacion_bloqueos = list(
        negocio.bloqueos.filter(
            esta_activo=True, fecha_inicio__lt=fin_dia, fecha_fin__gt=inicio_dia,
        ).values_list('fecha_inicio', 'fecha_fin', 'especialista_id')
    )
    return ocupacion_citas, ocupacion_bloqueos


def _ocupado_para(especialista_id, citas, bloqueos):
    """
    Lo que ocupa la agenda de un especialista: sus citas, las citas sin
    especialista y los bloqueos del negocio o suyos.
    """
    return [
        (inicio, fin) for inicio, fin, de in citas + bloqueos
        if de is None or de == especialista_id
    ]


def _horas_libres(fecha, horario, duracion_minutos, ocupados):
    """Horas ('HH:MM') en las que cabe una cita dentro del horario sin cruzarse"""
    if not horario:
        return []
    hora_apertura, hora_cierre = horario
    apertura = timezone.make_aware(datetime.combine(fecha, hora_apertura))
    cierre = timezone.make_aware(datetime.combine(fecha, hora_cierre))
    duracion = timedelta(minutes=duracion_minutos)
    ahora = timezone.now()

    if cierre <= ahora or apertura + duracion > cierre:
        return []

    # Primer horario: la apertura redondeada al siguiente intervalo (ej. 9:10 -> 9:30)
    minutos = apertura.hour * 60 + apertura.minute
    inicio = apertura + timedelta(minutes=(-minutos) % INTERVALO_MINUTOS)

    horas = []
    while inicio + duracion <= cierre:
        fin = inicio + duracion
        if inicio > ahora and not any(
            _se_traslapan(inicio, fin, ini_ocupado, fin_ocupado)
            for ini_ocupado, fin_ocupado in ocupados
        ):
            horas.append(timezone.localtime(inicio).strftime('%H:%M'))
        inicio += timedelta(minutes=INTERVALO_MINUTOS)
    return horas


def horarios_disponibles(negocio, fecha, duracion_minutos, excluir_cita_id=None,
                         especialista=None, servicio=None):
    """
    Lista de horas ('HH:MM') en las que se puede iniciar una cita de la
    duración indicada en la fecha dada.

    Un horario está disponible si:
    - Es futuro
    - La cita empieza y termina dentro del horario de atención
    - No se cruza con otra cita activa ni con un bloqueo de agenda

    Con varios especialistas: las horas de `especialista`, o si no se indica
    ("me da igual"), las horas en que al menos uno de los que hacen el
    servicio está libre.

    excluir_cita_id: al editar una cita, para que no choque consigo misma.
    """
    citas, bloqueos = _ocupacion_del_dia(negocio, fecha, excluir_cita_id)

    if not tiene_varios_especialistas(negocio):
        ocupados = [(inicio, fin) for inicio, fin, _ in citas + bloqueos]
        return _horas_libres(fecha, horario_del_dia(negocio, fecha), duracion_minutos, ocupados)

    candidatos = [especialista] if especialista else especialistas_para(negocio, servicio)
    horas = set()
    for candidato in candidatos:
        horas.update(_horas_libres(
            fecha, horario_especialista(candidato, fecha), duracion_minutos,
            _ocupado_para(candidato.id, citas, bloqueos),
        ))
    return sorted(horas)


def especialistas_libres(negocio, fecha_hora, duracion_minutos, servicio=None, excluir_cita_id=None):
    """Especialistas que hacen el servicio y están libres a esa hora (aware)"""
    local = timezone.localtime(fecha_hora)
    fecha, hora = local.date(), local.strftime('%H:%M')
    citas, bloqueos = _ocupacion_del_dia(negocio, fecha, excluir_cita_id)
    return [
        candidato for candidato in especialistas_para(negocio, servicio)
        if hora in _horas_libres(
            fecha, horario_especialista(candidato, fecha), duracion_minutos,
            _ocupado_para(candidato.id, citas, bloqueos),
        )
    ]


def elegir_especialista(negocio, fecha_hora, duracion_minutos, servicio=None, excluir_cita_id=None):
    """
    "Me da igual": el especialista libre con menos citas ese día (reparte el
    trabajo), o None si no hay ninguno libre.
    """
    from django.db.models import Count, Q

    libres = especialistas_libres(negocio, fecha_hora, duracion_minutos, servicio, excluir_cita_id)
    if not libres:
        return None
    dia = timezone.localtime(fecha_hora).date()
    carga = dict(
        negocio.especialistas.filter(id__in=[e.id for e in libres]).annotate(
            total=Count('citas', filter=Q(
                citas__fecha_hora__date=dia, citas__estado__in=ESTADOS_QUE_OCUPAN,
            ))
        ).values_list('id', 'total')
    )
    return min(libres, key=lambda e: (carga.get(e.id, 0), e.orden, e.nombre))


def esta_disponible(negocio, fecha_hora, duracion_minutos, excluir_cita_id=None,
                    especialista=None, servicio=None):
    """
    Verifica que se pueda agendar una cita que inicia en fecha_hora (aware).
    Usa exactamente los mismos horarios que se ofrecen en el calendario.
    """
    local = timezone.localtime(fecha_hora)
    return local.strftime('%H:%M') in horarios_disponibles(
        negocio, local.date(), duracion_minutos, excluir_cita_id,
        especialista=especialista, servicio=servicio,
    )


def resolver_especialista(negocio, fecha_hora, servicio, eleccion=None, excluir_cita_id=None):
    """
    Valida el horario y decide quién atiende. Retorna (disponible, especialista).

    - Una sola agenda: valida como siempre; si hay exactamente un especialista
      activo, la cita queda a su nombre (sirve si luego se agregan más).
    - Varios especialistas: `eleccion` es el id del elegido (debe hacer el
      servicio y estar libre) o vacío / 'cualquiera' ("me da igual": se asigna
      el libre con menos citas ese día).
    """
    duracion = servicio.duracion_minutos
    if not tiene_varios_especialistas(negocio):
        activos = especialistas_activos(negocio)
        disponible = esta_disponible(negocio, fecha_hora, duracion, excluir_cita_id)
        return disponible, (activos[0] if len(activos) == 1 else None)

    eleccion = str(eleccion or '')
    if eleccion.isdigit():
        elegido = next((e for e in especialistas_para(negocio, servicio) if e.id == int(eleccion)), None)
        if elegido is None:
            return False, None
        return esta_disponible(negocio, fecha_hora, duracion, excluir_cita_id, especialista=elegido), elegido

    elegido = elegir_especialista(negocio, fecha_hora, duracion, servicio, excluir_cita_id)
    return elegido is not None, elegido


def especialista_de_peticion(negocio, valor, servicio=None):
    """Especialista activo del negocio indicado en un parámetro (id), o None"""
    valor = str(valor or '')
    if not valor.isdigit() or not tiene_varios_especialistas(negocio):
        return None
    return next((e for e in especialistas_para(negocio, servicio) if e.id == int(valor)), None)
