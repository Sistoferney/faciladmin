"""
Tests de dar de baja clientes (no quieren volver)
"""
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.authentication.models import Usuario
from apps.citas.models import Cita
from apps.negocios.models import Negocio
from apps.servicios.models import Servicio

from .models import Cliente


@patch('apps.notificaciones.tasks.enviar_confirmacion_cita')
@override_settings(TWILIO_ACCOUNT_SID='', TWILIO_AUTH_TOKEN='')
class DarDeBajaClienteTests(TestCase):

    def setUp(self):
        self.admin = Usuario.objects.create_user(telefono='3000000000', password='x', nombre='A', email='a@a.com')
        self.negocio = Negocio.objects.create(administrador=self.admin, nombre='Spa', telefono='3000000000')
        self.servicio = Servicio.objects.create(
            negocio=self.negocio, nombre='Corte', precio=20000, duracion_minutos=30, frecuencia_dias=30
        )
        self.cliente = Cliente.objects.create(
            negocio=self.negocio, nombre='Ana', telefono='3001111111', email='ana@correo.com'
        )
        self.client.force_login(self.admin)
        self.url_baja = reverse('public:cliente_baja', args=[self.negocio.slug, self.cliente.id])

    def _cita(self, dias, estado='confirmada'):
        return Cita.objects.create(
            negocio=self.negocio, cliente=self.cliente, servicio=self.servicio,
            fecha_hora=timezone.now() + timedelta(days=dias), duracion_minutos=30, estado=estado,
        )

    def test_no_se_puede_con_citas_proximas(self, *mocks):
        cita = self._cita(3)
        resp = self.client.get(self.url_baja)
        self.assertContains(resp, 'tiene 1 cita próxima')
        self.assertContains(resp, reverse('public:cita_cancelar', args=[self.negocio.slug, cita.id]) + '?desde=clientes')
        self.assertNotContains(resp, 'name="motivo"')

        self.client.post(self.url_baja, {'motivo': 'x'})
        self.cliente.refresh_from_db()
        self.assertTrue(self.cliente.esta_activo)
        self.assertFalse(self.cliente.dar_de_baja())

    def test_citas_pasadas_o_canceladas_no_impiden(self, *mocks):
        self._cita(-10, estado='completada')
        self._cita(5, estado='cancelada')
        self.client.post(self.url_baja, {'motivo': 'No quiere volver'})
        self.cliente.refresh_from_db()
        self.assertFalse(self.cliente.esta_activo)
        self.assertEqual(self.cliente.motivo_baja, 'No quiere volver')
        self.assertIsNotNone(self.cliente.fecha_baja)
        # El historial se conserva
        self.assertEqual(self.cliente.citas.count(), 2)

    def test_dado_de_baja_no_recibe_mensajes(self, *mocks):
        from apps.notificaciones.services import elegir_canal
        self.assertEqual(elegir_canal(self.cliente), 'email')
        self.cliente.dar_de_baja()
        self.assertIsNone(elegir_canal(self.cliente))

    def test_desaparece_de_listas_y_seguimiento(self, *mocks):
        from apps.fidelizacion.recuperacion import seguimientos
        self._cita(-50, estado='completada')
        self.assertEqual(len(seguimientos(self.negocio)), 1)
        self.cliente.dar_de_baja()
        self.assertEqual(seguimientos(self.negocio), [])

        url_clientes = reverse('public:admin_clientes', args=[self.negocio.slug])
        self.assertNotContains(self.client.get(url_clientes), 'Ana')
        resp = self.client.get(url_clientes, {'baja': '1'})
        self.assertContains(resp, 'Ana')
        self.assertContains(resp, 'Reactivar')

    def test_reactivar(self, *mocks):
        self.cliente.dar_de_baja('se mudó')
        self.client.post(reverse('public:cliente_reactivar', args=[self.negocio.slug, self.cliente.id]))
        self.cliente.refresh_from_db()
        self.assertTrue(self.cliente.esta_activo)
        self.assertIsNone(self.cliente.fecha_baja)
        self.assertEqual(self.cliente.motivo_baja, '')

    def test_si_vuelve_a_agendar_se_reactiva(self, *mocks):
        from apps.negocios.disponibilidad import horarios_disponibles
        self.cliente.dar_de_baja()
        self.client.logout()
        fecha = timezone.localdate() + timedelta(days=3)
        hora = horarios_disponibles(self.negocio, fecha, 30)[0]
        self.client.post(reverse('public:agendar', args=[self.negocio.slug]), {
            'telefono': '3001111111', 'servicio': self.servicio.id,
            'fecha': fecha.isoformat(), 'hora': hora,
        })
        self.cliente.refresh_from_db()
        self.assertTrue(self.cliente.esta_activo)
        self.assertEqual(self.cliente.citas.count(), 1)

    def test_otro_negocio_no_puede(self, *mocks):
        otro = Usuario.objects.create_user(telefono='3009999999', password='x', nombre='O', email='o@o.com')
        Negocio.objects.create(administrador=otro, nombre='Otro', telefono='3009999999')
        self.client.force_login(otro)
        self.client.post(self.url_baja)
        self.cliente.refresh_from_db()
        self.assertTrue(self.cliente.esta_activo)
