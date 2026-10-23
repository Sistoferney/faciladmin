"""
IP real del cliente detrás de Cloudflare y del proxy de Railway

Camino en producción: visitante -> Cloudflare -> proxy de Railway -> Django.
REMOTE_ADDR es la IP del proxy de Railway (la misma para todos) y
X-Forwarded-For trae la lista de IPs por las que pasó la petición.

- La ÚLTIMA IP de X-Forwarded-For la agregó el proxy de Railway: es quien se
  le conectó. Las anteriores las puede escribir el propio cliente.
- Si esa IP es de Cloudflare, la petición pasó por Cloudflare y su
  encabezado CF-Connecting-IP (que Cloudflare siempre reescribe) trae la IP
  del visitante.
- Si no es de Cloudflare (alguien entró directo por *.up.railway.app),
  CF-Connecting-IP se ignora, porque lo pudo escribir el cliente, y se usa la
  última IP de X-Forwarded-For.

Se usa en los límites de intentos (RATELIMIT_IP_META_KEY en production.py)
y al registrar desde dónde se pidió una recuperación de contraseña.
"""
import ipaddress

from django.conf import settings

# Rangos publicados por Cloudflare (cloudflare.com/ips-v4 y /ips-v6).
# Cambian muy rara vez; si agregan uno nuevo, las visitas que lleguen por él
# se limitan por la IP de Cloudflare en vez de la del visitante (no se abre
# ningún hueco, solo el límite queda menos preciso).
RANGOS_CLOUDFLARE = [ipaddress.ip_network(rango) for rango in (
    '173.245.48.0/20', '103.21.244.0/22', '103.22.200.0/22', '103.31.4.0/22',
    '141.101.64.0/18', '108.162.192.0/18', '190.93.240.0/20', '188.114.96.0/20',
    '197.234.240.0/22', '198.41.128.0/17', '162.158.0.0/15', '104.16.0.0/13',
    '104.24.0.0/14', '172.64.0.0/13', '131.0.72.0/22',
    '2400:cb00::/32', '2606:4700::/32', '2803:f800::/32', '2405:b500::/32',
    '2405:8100::/32', '2a06:98c0::/29', '2c0f:f248::/32',
)]


def _ip_valida(valor):
    try:
        return ipaddress.ip_address(valor.strip())
    except ValueError:
        return None


def _es_de_cloudflare(ip):
    return any(ip in rango for rango in RANGOS_CLOUDFLARE)


def ip_cliente(request):
    """IP del visitante (detrás de los proxies si CONFIAR_EN_PROXY), o REMOTE_ADDR"""
    if getattr(settings, 'CONFIAR_EN_PROXY', False):
        reenviadas = request.META.get('HTTP_X_FORWARDED_FOR', '')
        conectada = _ip_valida(reenviadas.split(',')[-1]) if reenviadas else None
        if conectada:
            if _es_de_cloudflare(conectada):
                visitante = _ip_valida(request.META.get('HTTP_CF_CONNECTING_IP', ''))
                if visitante:
                    return str(visitante)
            return str(conectada)
    return request.META.get('REMOTE_ADDR', '')
