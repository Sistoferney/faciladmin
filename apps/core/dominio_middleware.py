"""
Redirección al dominio oficial (facilacces.com)

Los dominios anteriores (faciladmin.app) redirigen de forma permanente al
oficial, conservando la ruta: los enlaces viejos, los códigos QR impresos y
los mensajes ya enviados siguen funcionando.

Excepciones (se sirven también en el dominio anterior):
- /sw.js: el navegador no sigue redirecciones al actualizar un Service
  Worker; las apps instaladas en el dominio anterior deben poder seguir
  actualizándolo mientras sus usuarios pasan al nuevo.
- /static/: archivos que ese Service Worker tiene en caché.
- /health/: monitoreo.

Se activa con la variable DOMINIO_OFICIAL; sin ella no hace nada.
Para probar en local: DOMINIO_OFICIAL=localhost y DOMINIOS_REDIRIGIDOS=127.0.0.1
"""
from django.conf import settings
from django.http import HttpResponsePermanentRedirect

RUTAS_SIN_REDIRECCION = ('/sw.js', '/static/', '/health/')


class RedirigirPermanente308(HttpResponsePermanentRedirect):
    """308: como el 301, pero el navegador repite el POST con sus datos"""
    status_code = 308


class DominioOficialMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        oficial = getattr(settings, 'DOMINIO_OFICIAL', '')
        redirigidos = getattr(settings, 'DOMINIOS_REDIRIGIDOS', ())
        if oficial and redirigidos:
            host, _, puerto = request.META.get('HTTP_HOST', '').lower().partition(':')
            if host in redirigidos and not request.path.startswith(RUTAS_SIN_REDIRECCION):
                # Conserva protocolo y puerto tal como los ve el navegador (el
                # encabezado Host, no el puerto interno del servidor): en
                # producción https sin puerto; en local 127.0.0.1:8000 -> localhost:8000
                puerto = f':{puerto}' if puerto else ''
                destino = f'{request.scheme}://{oficial}{puerto}{request.get_full_path()}'
                if request.method in ('GET', 'HEAD'):
                    return HttpResponsePermanentRedirect(destino)
                return RedirigirPermanente308(destino)
        return self.get_response(request)
