"""
Protección del formulario de registro contra bots

Desde octubre de 2026 un bot llenaba el registro con nombres al azar,
teléfonos de EE. UU. y emails reales de terceros: facilacces terminaba
enviando "Activa tu cuenta" a desconocidos, lo que daña la reputación del
dominio (y con ella, la entrega de todos los emails). Filtros, en orden:

1. Campo trampa: un campo oculto que una persona no ve ni llena; los bots
   llenan todos los campos.
2. Tiempo mínimo: el formulario lleva una marca firmada de cuándo se mostró;
   nadie escribe nombre, apellido, teléfono y email en menos de 3 segundos.
3. Cloudflare Turnstile: verificación invisible de que es una persona.
   Se activa al configurar TURNSTILE_SITE_KEY y TURNSTILE_SECRET_KEY.

A los bots atrapados por 1 y 2 se les muestra la misma pantalla de éxito
que a una persona, para que no sepan qué los delató.
"""
import logging
import time

import requests
from django.conf import settings
from django.core import signing

logger = logging.getLogger(__name__)

CAMPO_TRAMPA = 'sitio_web'
CAMPO_MARCA = 'marca'
SEGUNDOS_MINIMOS = 3
_SAL_MARCA = 'suscripciones.registro'
URL_TURNSTILE = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'


def marca_formulario(momento=None):
    """Marca firmada con el momento en que se mostró el formulario"""
    return signing.dumps(momento if momento is not None else time.time(), salt=_SAL_MARCA)


def motivo_bot(datos):
    """
    Por qué el envío parece de un bot ('campo_trampa', 'sin_marca', 'muy_rapido'),
    o None si pasa los filtros
    """
    if datos.get(CAMPO_TRAMPA, '').strip():
        return 'campo_trampa'
    try:
        mostrado = signing.loads(datos.get(CAMPO_MARCA, ''), salt=_SAL_MARCA)
    except signing.BadSignature:
        return 'sin_marca'
    if time.time() - float(mostrado) < SEGUNDOS_MINIMOS:
        return 'muy_rapido'
    return None


def turnstile_activo():
    return bool(getattr(settings, 'TURNSTILE_SECRET_KEY', ''))


def turnstile_valido(token, ip):
    """
    Verifica con Cloudflare el token del widget. Sin claves configuradas no
    se exige. Si Cloudflare no responde, se deja pasar (los otros filtros
    siguen activos) para no bloquear registros reales por una caída ajena.
    """
    if not turnstile_activo():
        return True
    if not token:
        return False
    try:
        respuesta = requests.post(URL_TURNSTILE, data={
            'secret': settings.TURNSTILE_SECRET_KEY,
            'response': token,
            'remoteip': ip,
        }, timeout=5)
        return bool(respuesta.json().get('success'))
    except (requests.RequestException, ValueError):
        logger.warning('Turnstile no respondió; registro aceptado sin verificar')
        return True
