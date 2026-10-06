"""
Avisos de "Mis citas": qué cambió en las citas del cliente desde su última visita.

Respaldo de las notificaciones: si el cliente descartó el push, no tiene
canal configurado o el dueño le agendó la cita por teléfono, al abrir
"Mis citas" ve el cambio destacado.

Se guarda en la sesión (por negocio) una foto del estado de sus citas
próximas. La primera visita solo toma la foto: no avisa de lo anterior.
Lo que hace el propio cliente (editar, cancelar, enviar comprobante) se
registra en la foto al momento, para no avisarle de sus propios cambios.
"""
from django.utils import timezone

from apps.notificaciones.textos_push import a_la_hora, fecha_corta

CLAVE_SESION = 'citas_vistas'


def _estado(cita):
    abono = getattr(cita, 'abono', None)
    return {
        'estado': cita.estado,
        'abono': abono.estado if abono else '',
        'fecha': cita.fecha_hora.isoformat(),
    }


def _cuando(cita):
    return f'{fecha_corta(cita.fecha_hora, con_hora=False)} {a_la_hora(cita.fecha_hora)}'


def _fotos(request):
    return request.session.get(CLAVE_SESION, {})


def _guardar(request, negocio, foto):
    fotos = _fotos(request)
    fotos[str(negocio.id)] = foto
    request.session[CLAVE_SESION] = fotos


def _avisos_de(cita, antes):
    """Avisos de una cita comparada con como estaba en la visita anterior"""
    servicio = cita.servicio.nombre
    ahora = _estado(cita)

    if antes is None:
        # Cita que no estaba la vez anterior: solo se avisa si la agendó el negocio
        if cita.origen != 'web':
            return [('info', f'{cita.negocio.nombre} te agendó {servicio} para el {_cuando(cita)}.')]
        return []

    if ahora['estado'] != antes['estado']:
        if ahora['estado'] == 'cancelada':
            return [('danger', f'Tu cita de {servicio} del {_cuando(cita)} fue cancelada.')]
        if ahora['estado'] == 'confirmada' and antes['estado'] == 'pendiente_abono':
            return [('success', f'Tu cita de {servicio} del {_cuando(cita)} fue confirmada.')]

    avisos = []
    if ahora['fecha'] != antes['fecha']:
        avisos.append(('info', f'Tu cita de {servicio} cambió para el {_cuando(cita)}.'))
    if ahora['abono'] != antes['abono']:
        if ahora['abono'] == 'rechazado':
            avisos.append(('warning', f'No pudimos validar tu pago de {servicio}. Envía un nuevo comprobante.'))
        elif ahora['abono'] in ('confirmado', 'exonerado') and ahora['estado'] == antes['estado']:
            avisos.append(('success', f'Tu pago de {servicio} del {_cuando(cita)} fue confirmado.'))
    return avisos


def novedades(request, negocio, citas):
    """
    Lista de (tipo, texto) con los cambios desde la última visita, y
    actualiza la foto. `citas`: todas las citas del cliente en el negocio.
    """
    ahora = timezone.now()
    proximas = [c for c in citas if c.fecha_hora > ahora]
    anterior = _fotos(request).get(str(negocio.id))

    avisos = []
    if anterior is not None:
        for cita in sorted(proximas, key=lambda c: c.fecha_hora):
            avisos += _avisos_de(cita, anterior.get(str(cita.id)))

    # Solo citas próximas (las pasadas no generan avisos). Las canceladas
    # también se guardan, para no repetir el aviso en la siguiente visita.
    _guardar(request, negocio, {str(c.id): _estado(c) for c in proximas})
    return avisos


def registrar_cambio_propio(request, cita):
    """El cliente cambió su cita: actualizar la foto para no avisarle de eso mismo"""
    foto = _fotos(request).get(str(cita.negocio_id))
    if foto is None:
        return
    from apps.citas.models import Cita
    cita = Cita.objects.select_related('abono').get(pk=cita.pk)  # estado ya guardado
    foto[str(cita.id)] = _estado(cita)
    _guardar(request, cita.negocio, foto)
