"""
Textos de las notificaciones push: cortos y "limpios".

Chrome para Android oculta como "posible spam" las notificaciones que parecen
publicidad (muchos emojis, teléfonos, precios, enlaces). Por eso los push
llevan una sola línea con lo esencial; el detalle completo (precio, datos de
pago, teléfono) está en la app al tocar la notificación, y en los mensajes por
email/SMS/WhatsApp, que conservan su formato largo.
"""
from django.utils import timezone

DIAS = ['lun', 'mar', 'mié', 'jue', 'vie', 'sáb', 'dom']
MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']


def hora_corta(fecha_hora):
    """13:30 -> '1:30 p. m.' (hora de Colombia)"""
    local = timezone.localtime(fecha_hora)
    hora = local.hour % 12 or 12
    sufijo = 'a. m.' if local.hour < 12 else 'p. m.'
    return f'{hora}:{local.minute:02d} {sufijo}'


def a_la_hora(fecha_hora):
    """'a la 1:30 p. m.' / 'a las 3:00 p. m.'"""
    articulo = 'la' if timezone.localtime(fecha_hora).hour % 12 == 1 else 'las'
    return f'a {articulo} {hora_corta(fecha_hora)}'


def fecha_corta(fecha_hora, con_hora=True):
    """'sáb 5 oct, 1:30 p. m.' (hora de Colombia)"""
    local = timezone.localtime(fecha_hora)
    texto = f'{DIAS[local.weekday()]} {local.day} {MESES[local.month - 1]}'
    return f'{texto}, {hora_corta(fecha_hora)}' if con_hora else texto


def _frase(texto):
    """Evita el doble punto cuando la frase termina en la hora ('p. m..')"""
    return texto.replace('m..', 'm.')


def resumen_cita(cita):
    """'Ana López · Masaje · sáb 5 oct, 1:30 p. m.' (para el dueño)"""
    return f'{cita.cliente.nombre} · {cita.servicio.nombre} · {fecha_corta(cita.fecha_hora)}'


# ---------- Avisos al dueño ----------

def push_dueno_nueva_cita(cita):
    return 'Nueva cita', resumen_cita(cita)


def push_dueno_cita_modificada(cita):
    return 'Cita modificada', (
        f'{cita.cliente.nombre} la movió al {fecha_corta(cita.fecha_hora)} · {cita.servicio.nombre}'
    )


def push_dueno_cita_cancelada(cita):
    return 'Cita cancelada', resumen_cita(cita)


def push_dueno_abono_vencido(cita):
    return 'Abono vencido', (
        f'{cita.cliente.nombre} no ha pagado el abono · {cita.servicio.nombre}, '
        f'{fecha_corta(cita.fecha_hora, con_hora=False)}'
    )


def push_dueno_comprobante(cita):
    return 'Comprobante recibido', (
        f'{cita.cliente.nombre} envió su comprobante · {cita.servicio.nombre}, '
        f'{fecha_corta(cita.fecha_hora, con_hora=False)}'
    )


# ---------- Avisos al cliente ----------

def push_cliente(tipo, cita, negocio, asunto=''):
    """
    (título, cuerpo) del push al cliente según el tipo de notificación.
    El título es el nombre del negocio; el cuerpo, una frase corta.
    """
    if cita is None:
        # Sugerencias, reactivación, promociones: sin cita asociada
        return negocio.nombre, (asunto.split(' - ')[0] if asunto else 'Tienes un mensaje nuevo')

    servicio = cita.servicio.nombre
    fecha = fecha_corta(cita.fecha_hora)
    dia = fecha_corta(cita.fecha_hora, con_hora=False)

    if cita.estado == 'pendiente_abono':
        confirmacion = f'Tu cita de {servicio} quedó agendada para el {fecha}. Recuerda pagar el abono para confirmarla.'
    else:
        confirmacion = f'Tu cita de {servicio} está confirmada para el {fecha}.'

    textos = {
        'confirmacion_cita': confirmacion,
        'recordatorio_cita': f'Te esperamos mañana {a_la_hora(cita.fecha_hora)} para tu {servicio}.',
        'recordatorio_2h': f'Tu cita de {servicio} es hoy {a_la_hora(cita.fecha_hora)}. ¡Te esperamos!',
        'recordatorio_abono': f'Recuerda pagar el abono de tu cita del {dia} para confirmarla.',
        'confirmacion_abono': f'Recibimos tu pago. Tu cita del {fecha} está confirmada.',
        'cancelacion': f'Tu cita de {servicio} del {fecha} fue cancelada.',
        'abono_rechazado': f'No pudimos validar el pago de tu cita del {dia}. Revisa Mis citas.',
    }
    return negocio.nombre, _frase(textos.get(tipo, f'Novedades sobre tu cita del {fecha}.'))
