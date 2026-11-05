"""
Posicionamiento en buscadores (Google, Bing)

- robots.txt: permite las páginas públicas (portada y mini-páginas de los
  negocios) y bloquea las privadas (paneles, APIs, login, "Mis citas").
- sitemap.xml: lista de páginas públicas para que Google las encuentre.
- Datos estructurados (JSON-LD, schema.org): le dicen a Google qué es cada
  página (la plataforma, o un negocio de belleza con dirección, teléfono,
  horario y servicios) para mostrarla mejor en los resultados.

Todas las direcciones usan el dominio oficial (facilacces.com).
"""
import json
from xml.sax.saxutils import escape

from django.conf import settings
from django.http import HttpResponse
from django.utils.safestring import mark_safe

# Páginas públicas de la plataforma (ruta, prioridad)
PAGINAS_PLATAFORMA = [
    ('/', '1.0'),
    ('/como-funciona/', '0.8'),
    ('/precios/', '0.8'),
    ('/registro/', '0.7'),
    ('/contacto/', '0.5'),
]

# Tipo de negocio -> tipo de schema.org
TIPOS_SCHEMA = {
    'spa': 'DaySpa',
    'peluqueria': 'HairSalon',
    'barberia': 'HairSalon',
    'salon_belleza': 'BeautySalon',
}
TIPO_SCHEMA_DEFECTO = 'HealthAndBeautyBusiness'

DIAS_SCHEMA = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


def url_base(request):
    """https://facilacces.com (o el dominio de la petición si no hay oficial)"""
    oficial = getattr(settings, 'DOMINIO_OFICIAL', '')
    if oficial and oficial not in ('localhost', '127.0.0.1'):
        return f'https://{oficial}'
    return f'{request.scheme}://{request.get_host()}'


def robots_txt(request):
    contenido = f"""# robots.txt - facilacces
User-agent: *
Allow: /
Disallow: /admin/
Disallow: /superadmin/
Disallow: /api/
Disallow: /login/
Disallow: /recuperar-password/
Disallow: /*/admin/
Disallow: /*/mis-citas/

Sitemap: {url_base(request)}/sitemap.xml
"""
    return HttpResponse(contenido, content_type='text/plain; charset=utf-8')


def sitemap_xml(request):
    from apps.negocios.models import Negocio

    base = url_base(request)
    entradas = [(f'{base}{ruta}', None, prioridad) for ruta, prioridad in PAGINAS_PLATAFORMA]
    for slug, actualizado in Negocio.objects.filter(esta_activo=True).values_list('slug', 'fecha_actualizacion'):
        fecha = actualizado.date().isoformat() if actualizado else None
        entradas.append((f'{base}/{slug}/', fecha, '0.9'))
        entradas.append((f'{base}/{slug}/agendar/', fecha, '0.6'))

    lineas = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, fecha, prioridad in entradas:
        lineas.append('  <url>')
        lineas.append(f'    <loc>{escape(url)}</loc>')
        if fecha:
            lineas.append(f'    <lastmod>{fecha}</lastmod>')
        lineas.append(f'    <priority>{prioridad}</priority>')
        lineas.append('  </url>')
    lineas.append('</urlset>')
    return HttpResponse('\n'.join(lineas), content_type='application/xml; charset=utf-8')


def json_ld(datos):
    """<script type="application/ld+json"> seguro (los textos vienen de los negocios)"""
    texto = json.dumps(datos, ensure_ascii=False)
    texto = texto.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    return mark_safe(f'<script type="application/ld+json">{texto}</script>')


def datos_plataforma(base, logo):
    return [
        {
            '@context': 'https://schema.org',
            '@type': 'Organization',
            'name': 'facilacces',
            'url': f'{base}/',
            'logo': logo,
        },
        {
            '@context': 'https://schema.org',
            '@type': 'SoftwareApplication',
            'name': 'facilacces',
            'url': f'{base}/',
            'applicationCategory': 'BusinessApplication',
            'operatingSystem': 'Web, Android, iOS',
            'description': (
                'Agenda online para spas, peluquerías, barberías y salones de belleza: '
                'reservas 24/7, recordatorios automáticos, abonos y gestión de clientes.'
            ),
            'inLanguage': 'es-CO',
        },
    ]


def _absoluta(base, url):
    return f'{base}{url}' if url.startswith('/') else url


def datos_negocio(negocio, base):
    """Negocio de belleza (LocalBusiness) con dirección, contacto, horario y servicios"""
    url = f'{base}/{negocio.slug}/'
    datos = {
        '@context': 'https://schema.org',
        '@type': TIPOS_SCHEMA.get(negocio.tipo, TIPO_SCHEMA_DEFECTO),
        'name': negocio.nombre,
        'url': url,
        'telephone': negocio.telefono,
        'potentialAction': {
            '@type': 'ReserveAction',
            'target': f'{base}/{negocio.slug}/agendar/',
        },
    }
    if negocio.descripcion:
        datos['description'] = negocio.descripcion[:300]
    imagenes = [_absoluta(base, img.url) for img in (negocio.imagen_portada, negocio.logo) if img]
    if imagenes:
        datos['image'] = imagenes
    if negocio.logo:
        datos['logo'] = _absoluta(base, negocio.logo.url)
    if negocio.direccion or negocio.ciudad:
        datos['address'] = {
            '@type': 'PostalAddress',
            'streetAddress': negocio.direccion,
            'addressLocality': negocio.ciudad,
            'addressRegion': negocio.estado,
            'postalCode': negocio.codigo_postal,
            'addressCountry': 'CO',
        }
        datos['address'] = {k: v for k, v in datos['address'].items() if v}
    redes = [r for r in (negocio.facebook, negocio.instagram, negocio.tiktok, negocio.twitter) if r]
    if redes:
        datos['sameAs'] = redes

    horario = _horario(negocio)
    if horario:
        datos['openingHoursSpecification'] = horario

    servicios = list(negocio.servicios.filter(esta_activo=True).order_by('orden', 'nombre')[:30])
    if servicios:
        datos['hasOfferCatalog'] = {
            '@type': 'OfferCatalog',
            'name': 'Servicios',
            'itemListElement': [
                {
                    '@type': 'Offer',
                    'itemOffered': {'@type': 'Service', 'name': s.nombre},
                    'price': str(int(s.precio)),
                    'priceCurrency': 'COP',
                }
                for s in servicios
            ],
        }
    return datos


def _horario(negocio):
    """Horario por día (configuración por día de la semana) en formato schema.org"""
    especificacion = []
    for config in negocio.configuraciones_horario.filter(esta_abierto=True).order_by('dia_semana'):
        if 0 <= config.dia_semana < 7:
            especificacion.append({
                '@type': 'OpeningHoursSpecification',
                'dayOfWeek': DIAS_SCHEMA[config.dia_semana],
                'opens': config.hora_apertura.strftime('%H:%M'),
                'closes': config.hora_cierre.strftime('%H:%M'),
            })
    return especificacion
