"""
Tests de abonos: al vencer, el dueño decide si confirma el pago o cancela la cita
"""
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.authentication.models import Usuario
from apps.citas.models import Cita
from apps.clientes.models import Cliente
from apps.negocios.models import Negocio
from apps.servicios.models import Servicio

from .models import Abono
from .tasks import verificar_abonos_pendientes


@patch('apps.citas.signals.enviar_confirmacion_cita', create=True)
class AbonoVencidoTests(TestCase):

    def setUp(self):
        admin = Usuario.objects.create_user(
            telefono='3000000000', password='x', nombre='Admin', email='a@a.com'
        )
        self.negocio = Negocio.objects.create(administrador=admin, nombre='Spa', telefono='3000000000')
        servicio = Servicio.objects.create(
            negocio=self.negocio, nombre='Masaje', precio=50000, duracion_minutos=60
        )
        cliente = Cliente.objects.create(negocio=self.negocio, nombre='Ana', telefono='3001111111')
        self.cita = Cita.objects.create(
            negocio=self.negocio, cliente=cliente, servicio=servicio,
            fecha_hora=timezone.now() + timedelta(days=1), duracion_minutos=60,
            estado='pendiente_abono',
        )
        self.abono = Abono.objects.create(
            cita=self.cita, monto=20000, metodo_pago='transferencia', estado='pendiente',
            fecha_limite=timezone.now() - timedelta(hours=1),
        )
        self.client.force_login(admin)

    @patch('apps.notificaciones.services.NotificacionService.enviar_push',
           return_value={'success': True})
    def test_al_vencer_avisa_al_dueno_y_no_cancela_la_cita(self, enviar_push, *mocks):
        verificar_abonos_pendientes()

        self.abono.refresh_from_db()
        self.cita.refresh_from_db()
        self.assertEqual(self.abono.estado, 'vencido')
        self.assertEqual(self.cita.estado, 'pendiente_abono')
        self.assertTrue(enviar_push.call_args.kwargs['enviar_a_admin'])
        self.assertIn('Ana', enviar_push.call_args.kwargs['mensaje'])

    def test_panel_muestra_vencidos_por_defecto_con_acciones(self, *mocks):
        self.abono.estado = 'vencido'
        self.abono.save()
        resp = self.client.get(reverse('public:abonos_admin', args=[self.negocio.slug]))
        self.assertContains(resp, 'Vencido')
        self.assertContains(
            resp, reverse('public:cita_cancelar', args=[self.negocio.slug, self.cita.id]) + '?desde=abonos'
        )
        self.assertContains(resp, reverse('public:abono_confirmar', args=[self.negocio.slug, self.abono.id]))

    def test_dueno_cancela_cita_desde_abonos(self, *mocks):
        url = reverse('public:cita_cancelar', args=[self.negocio.slug, self.cita.id]) + '?desde=abonos'
        resp = self.client.post(url, {'motivo': 'No pagó el abono'})
        self.assertRedirects(resp, reverse('public:abonos_admin', args=[self.negocio.slug]))
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.estado, 'cancelada')
        self.assertIn('No pagó el abono', self.cita.notas_internas)

    def test_dueno_confirma_pago_tardio(self, *mocks):
        self.abono.estado = 'vencido'
        self.abono.save()
        self.client.post(reverse('public:abono_confirmar', args=[self.negocio.slug, self.abono.id]))
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.estado, 'confirmada')
