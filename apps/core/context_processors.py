"""
Variables disponibles en todas las plantillas
"""
from django.conf import settings


def dominio_oficial(request):
    """
    URL base del dominio oficial (https://facilacces.com) y dirección
    canónica de la página actual.

    Las vistas previas en redes (WhatsApp, Facebook, Instagram) y los
    buscadores usan la canónica: aunque se comparta un enlace de
    faciladmin.app, la tarjeta y la dirección oficial son de facilacces.com.
    Sin DOMINIO_OFICIAL se usa el dominio de la petición.
    """
    oficial = getattr(settings, 'DOMINIO_OFICIAL', '')
    if oficial:
        url_base = f'{request.scheme}://{oficial}'
        puerto = request.META.get('HTTP_HOST', '').partition(':')[2]
        if puerto and oficial in ('localhost', '127.0.0.1'):
            url_base += f':{puerto}'  # prueba local
    else:
        url_base = f'{request.scheme}://{request.get_host()}'
    return {
        'url_base': url_base,
        'url_canonica': f'{url_base}{request.path}',
    }
