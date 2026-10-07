"""
Listado de negocios del superadministrador y modo soporte en el panel
"""
from datetime import timedelta

from django.test import TestCase
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
