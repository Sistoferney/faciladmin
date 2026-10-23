"""
Listado de negocios del superadministrador y modo soporte en el panel
"""
from datetime import timedelta

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.authentication.models import Usuario
from apps.citas.models import Cita
from apps.clientes.models import Cliente
from apps.negocios.models import Negocio
from apps.servicios.models import Servicio


def _negocio(nombre, telefono):
    dueno = Usuario.objects.create_user(
        telefono=telefono, password='x', nombre=f'Dueño {nombre}', email=f'{telefono}@correo.com'
    )
    return Negocio.objects.create(administrador=dueno, nombre=nombre, telefono=telefono)


class NegociosSuperadminTests(TestCase):

    def setUp(self):
        self.superadmin = Usuario.objects.create_superuser(
            telefono='3007794375', password='x', nombre='Super', email='super@correo.com'
        )
        self.activo = _negocio('Spa Activo', '3001000001')
        self.dormido = _negocio('Spa Dormido', '3001000002')
        servicio = Servicio.objects.create(negocio=self.activo, nombre='Corte', precio=10000, duracion_minutos=30)
        cliente = Cliente.objects.create(negocio=self.activo, nombre='Ana', telefono='3002000001')
        for dias in (2, 3):
            Cita.objects.create(
                negocio=self.activo, cliente=cliente, servicio=servicio,
                fecha_hora=timezone.now() + timedelta(days=dias), duracion_minutos=30, estado='confirmada',
            )
        self.url = reverse('core:superadmin_negocios')

    def _negocios(self, **params):
        self.client.force_login(self.superadmin)
        return {n.nombre: n for n in self.client.get(self.url, params).context['pagina']}

    def test_solo_superadmin(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)  # al login
        self.client.force_login(self.activo.administrador)
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_indicadores_de_uso(self):
        negocios = self._negocios()
        self.assertEqual(negocios['Spa Activo'].citas_30d, 2)
        self.assertEqual(negocios['Spa Activo'].total_clientes, 1)
        self.assertEqual(negocios['Spa Dormido'].citas_30d, 0)
        self.assertTrue(negocios['Spa Activo'].whatsapp_dueno.startswith('https://wa.me/573001000001'))

    def test_sin_actividad(self):
        negocios = self._negocios(estado='sin_actividad')
        self.assertEqual(list(negocios), ['Spa Dormido'])
        resumen = self.client.get(self.url).context['resumen']
        self.assertEqual(resumen['sin_actividad'], 1)
        self.assertEqual(resumen['total'], 2)

    def test_busca_por_celular_del_dueno(self):
        self.assertEqual(list(self._negocios(q='300 100 0002')), ['Spa Dormido'])
        self.assertEqual(list(self._negocios(q='activo')), ['Spa Activo'])

    def test_login_del_superadmin_va_a_negocios(self):
        self.client.force_login(self.superadmin)
        self.assertRedirects(self.client.get(reverse('core:dashboard_redirect')), self.url)

    def test_panel_en_modo_soporte(self):
        self.client.force_login(self.superadmin)
        resp = self.client.get(reverse('public:admin_dashboard', args=[self.activo.slug]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Modo soporte')
        # Su dispositivo no se suscribe a los avisos del negocio
        self.assertNotContains(resp, 'js/pwa-register.js"></script>')
        self.assertNotContains(resp, 'rel="manifest"')

    def test_dueno_no_ve_modo_soporte(self):
        self.client.force_login(self.activo.administrador)
        resp = self.client.get(reverse('public:admin_dashboard', args=[self.activo.slug]))
        self.assertNotContains(resp, 'Modo soporte')
        self.assertContains(resp, 'js/pwa-register.js"></script>')


@override_settings(
    DOMINIO_OFICIAL='facilacces.com',
    DOMINIOS_REDIRIGIDOS=('faciladmin.app', 'www.faciladmin.app'),
    ALLOWED_HOSTS=['facilacces.com', 'faciladmin.app', 'www.faciladmin.app', 'testserver'],
)
class DominioOficialTests(TestCase):

    def test_redirige_conservando_la_ruta(self):
        resp = self.client.get('/spa-ilusion/mis-citas/?x=1', HTTP_HOST='faciladmin.app', secure=True)
        self.assertEqual(resp.status_code, 301)
        self.assertEqual(resp['Location'], 'https://facilacces.com/spa-ilusion/mis-citas/?x=1')

    @override_settings(DOMINIO_OFICIAL='localhost', DOMINIOS_REDIRIGIDOS=('127.0.0.1',),
                       ALLOWED_HOSTS=['localhost', '127.0.0.1'])
    def test_en_local_conserva_el_puerto(self):
        resp = self.client.get('/precios/', HTTP_HOST='127.0.0.1:8000')
        self.assertEqual(resp['Location'], 'http://localhost:8000/precios/')

    def test_post_conserva_el_metodo(self):
        resp = self.client.post('/login/', {'a': 1}, HTTP_HOST='www.faciladmin.app')
        self.assertEqual(resp.status_code, 308)

    def test_service_worker_y_estaticos_no_se_redirigen(self):
        # El navegador no sigue redirecciones al actualizar el Service Worker
        self.assertEqual(self.client.get('/sw.js', HTTP_HOST='faciladmin.app').status_code, 200)
        resp = self.client.get('/static/js/sw.js', HTTP_HOST='faciladmin.app')
        self.assertNotIn(resp.status_code, (301, 308))

    def test_dominio_oficial_no_se_redirige(self):
        self.assertEqual(self.client.get('/', HTTP_HOST='facilacces.com').status_code, 200)

    @override_settings(DOMINIO_OFICIAL='')
    def test_sin_configurar_no_hace_nada(self):
        self.assertEqual(self.client.get('/', HTTP_HOST='faciladmin.app').status_code, 200)


@override_settings(
    DOMINIO_OFICIAL='facilacces.com',
    DOMINIOS_REDIRIGIDOS=(),
    ALLOWED_HOSTS=['facilacces.com', 'faciladmin.app', 'testserver'],
)
class VistaPreviaRedesTests(TestCase):
    """Al compartir en redes, la tarjeta y la dirección oficial son de facilacces.com"""

    def test_portada(self):
        resp = self.client.get('/precios/', HTTP_HOST='faciladmin.app', secure=True)
        self.assertContains(resp, '<link rel="canonical" href="https://facilacces.com/precios/">')
        self.assertContains(resp, 'content="https://facilacces.com/static/images/facilacces-og.png"')
        self.assertContains(resp, 'og:title')

    def test_minipagina_usa_datos_del_negocio(self):
        negocio = _negocio('Spa Ilusión', '3001000001')
        negocio.descripcion = 'Uñas y pestañas en Bogotá'
        negocio.save()
        resp = self.client.get(f'/{negocio.slug}/', HTTP_HOST='facilacces.com', secure=True)
        self.assertContains(resp, f'<link rel="canonical" href="https://facilacces.com/{negocio.slug}/">')
        self.assertContains(resp, 'content="Spa Ilusión · Agenda tu cita"')
        self.assertContains(resp, 'content="Uñas y pestañas en Bogotá"')


@override_settings(DOMINIO_OFICIAL='facilacces.com', DOMINIOS_REDIRIGIDOS=(),
                   ALLOWED_HOSTS=['facilacces.com', 'testserver'])
class BuscadoresTests(TestCase):
    """Google puede indexar las páginas públicas, no las privadas"""

    def setUp(self):
        self.negocio = _negocio('Spa Ilusión', '3001000001')
        self.negocio.ciudad = 'Bogotá'
        self.negocio.save()
        Servicio.objects.create(negocio=self.negocio, nombre='Manicure', precio=20000, duracion_minutos=60)

    def _get(self, url):
        return self.client.get(url, HTTP_HOST='facilacces.com', secure=True)

    def test_robots_permite_publicas_y_bloquea_privadas(self):
        texto = self._get('/robots.txt').content.decode()
        self.assertIn('Allow: /', texto)
        self.assertNotIn('Disallow: /\n', texto)
        self.assertIn('Disallow: /*/admin/', texto)
        self.assertIn('Disallow: /*/mis-citas/', texto)
        self.assertIn('Sitemap: https://facilacces.com/sitemap.xml', texto)

    def test_sitemap_incluye_minipaginas_activas(self):
        inactivo = _negocio('Cerrado', '3001000002')
        inactivo.esta_activo = False
        inactivo.save()
        texto = self._get('/sitemap.xml').content.decode()
        self.assertIn('<loc>https://facilacces.com/</loc>', texto)
        self.assertIn(f'<loc>https://facilacces.com/{self.negocio.slug}/</loc>', texto)
        self.assertNotIn(f'/{inactivo.slug}/', texto)

    def test_portada_indexable_con_datos_estructurados(self):
        resp = self._get('/')
        self.assertContains(resp, '<meta name="robots" content="index, follow">')
        self.assertContains(resp, '"@type": "SoftwareApplication"')

    def test_minipagina_indexable_como_negocio_local(self):
        resp = self._get(f'/{self.negocio.slug}/')
        self.assertContains(resp, '<meta name="robots" content="index, follow">')
        self.assertContains(resp, '"@type": "DaySpa"')
        self.assertContains(resp, '"addressLocality": "Bogotá"')
        self.assertContains(resp, '"name": "Manicure"')
        self.assertContains(resp, 'Spa Ilusión | Spa en Bogotá')

    def test_paginas_privadas_no_indexables(self):
        resp = self._get(f'/{self.negocio.slug}/mis-citas/')
        self.assertContains(resp, '<meta name="robots" content="noindex, nofollow">')

    def test_datos_estructurados_escapan_html(self):
        self.negocio.descripcion = '</script><script>alert(1)</script>'
        self.negocio.save()
        resp = self._get(f'/{self.negocio.slug}/')
        self.assertNotContains(resp, '</script><script>alert(1)')


class IpClienteTests(TestCase):
    """IP del visitante para los límites de intentos (ver apps/core/red.py)"""

    def _ip(self, **meta):
        from django.test import RequestFactory
        from apps.core.red import ip_cliente
        return ip_cliente(RequestFactory().get('/', **meta))

    @override_settings(CONFIAR_EN_PROXY=True)
    def test_toma_la_ip_que_agrego_el_proxy(self):
        # La primera la escribió el cliente: no sirve para saltarse el límite
        self.assertEqual(self._ip(HTTP_X_FORWARDED_FOR='1.1.1.1, 200.1.2.3', REMOTE_ADDR='10.0.0.1'), '200.1.2.3')

    @override_settings(CONFIAR_EN_PROXY=True)
    def test_detras_de_cloudflare_usa_cf_connecting_ip(self):
        # 104.16.0.1 es de Cloudflare: la petición pasó por ahí
        self.assertEqual(self._ip(
            HTTP_X_FORWARDED_FOR='1.1.1.1, 200.1.2.3, 104.16.0.1',
            HTTP_CF_CONNECTING_IP='200.1.2.3', REMOTE_ADDR='10.0.0.1',
        ), '200.1.2.3')

    @override_settings(CONFIAR_EN_PROXY=True)
    def test_cf_connecting_ip_falso_se_ignora_sin_cloudflare(self):
        # Entró directo por *.up.railway.app escribiendo el encabezado a mano
        self.assertEqual(self._ip(
            HTTP_X_FORWARDED_FOR='200.1.2.3', HTTP_CF_CONNECTING_IP='9.9.9.9', REMOTE_ADDR='10.0.0.1',
        ), '200.1.2.3')

    @override_settings(CONFIAR_EN_PROXY=True)
    def test_sin_encabezado_o_invalido_usa_remote_addr(self):
        self.assertEqual(self._ip(REMOTE_ADDR='10.0.0.1'), '10.0.0.1')
        self.assertEqual(self._ip(HTTP_X_FORWARDED_FOR='basura', REMOTE_ADDR='10.0.0.1'), '10.0.0.1')

    @override_settings(CONFIAR_EN_PROXY=False)
    def test_sin_proxy_ignora_el_encabezado(self):
        self.assertEqual(self._ip(HTTP_X_FORWARDED_FOR='200.1.2.3', REMOTE_ADDR='127.0.0.1'), '127.0.0.1')
