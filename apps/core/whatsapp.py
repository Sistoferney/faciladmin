"""
Enlaces de WhatsApp (wa.me) para contactar al negocio o al cliente

wa.me exige el número en formato internacional sin '+' (573001234567).
Los números se normalizan igual que los teléfonos de usuario, así un número
guardado como "300 123 4567" (sin código de país) también funciona.
"""
from urllib.parse import quote

from apps.authentication.telefonos import normalizar_telefono


def numero_whatsapp(valor):
    """'300 123 4567' -> '573001234567', o '' si no es un número válido"""
    normalizado = normalizar_telefono(valor)
    return normalizado.lstrip('+') if normalizado else ''


def enlace_whatsapp(valor, texto=''):
    """URL de wa.me con el mensaje prellenado, o '' si el número no es válido"""
    numero = numero_whatsapp(valor)
    if not numero:
        return ''
    url = f'https://wa.me/{numero}'
    return f'{url}?text={quote(texto)}' if texto else url


def contacto_negocio(negocio):
    """Número de WhatsApp del negocio (o su teléfono si no configuró WhatsApp)"""
    return negocio.whatsapp or negocio.telefono


def enlace_cliente_a_negocio(cita):
    """El cliente escribe al negocio sobre su cita"""
    from django.utils import timezone
    fecha = timezone.localtime(cita.fecha_hora)
    texto = (
        f'Hola {cita.negocio.nombre}, tengo una duda sobre mi cita de '
        f'{cita.servicio.nombre} del {fecha.strftime("%d/%m/%Y a las %H:%M")}.'
    )
    return enlace_whatsapp(contacto_negocio(cita.negocio), texto)


def enlace_negocio_a_cliente(cita):
    """El dueño escribe al cliente sobre su cita"""
    from django.utils import timezone
    fecha = timezone.localtime(cita.fecha_hora)
    texto = (
        f'Hola {cita.cliente.nombre}, te escribimos de {cita.negocio.nombre} sobre tu cita de '
        f'{cita.servicio.nombre} del {fecha.strftime("%d/%m/%Y a las %H:%M")}.'
    )
    return enlace_whatsapp(cita.cliente.telefono, texto)
