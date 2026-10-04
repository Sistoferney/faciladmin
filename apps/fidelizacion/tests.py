"""
Tests del seguimiento de clientes según la frecuencia de su servicio
(servicio cada 30 días: recordatorio a los 32, por recuperar a los 45)
"""
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.authentication.models import Usuario
from apps.citas.models import Cita
from apps.clientes.models import Cliente
from apps.negocios.models import Negocio
from apps.notificaciones.models import Notificacion
from apps.servicios.models import Servicio

from .recuperacion import clientes_por_recuperar, seguimientos
from .tasks import sugerir_proximas_citas


@patch('apps.notificaciones.tasks.enviar_confirmacion_cita')
@override_settings(TWILIO_ACCOUNT_SID='', TWILIO_AUTH_TOKEN='')
class SeguimientoPorFrecuenciaTests(TestCase):

    def setUp(self):
        self.admin = Usuario.objects.create_user(telefono='3000000000', password='x', nombre='A', email='a@a.com')
        self.negocio = Negocio.objects.create(administrador=self.admin, nombre='Spa', telefono='3000000000')
        self.corte = Servicio.objects.create(
            negocio=self.negocio, nombre='Corte', precio=20000, duracion_minutos=30, frecuencia_dias=30
        )
        self.sin_frecuencia = Servicio.objects.create(
            negocio=self.negocio, nombre='Manicure', precio=20000, duracion_minutos=30
        )
        self._n = 0

    def _cliente_con_visita(self, hace_dias, servicio=None, **extra):
        self._n += 1
        cliente = Cliente.objects.create(
            negocio=self.negocio, nombre=f'Cliente {self._n}', telefono=f'30011111{self._n:02d}',
            email=f'c{self._n}@correo.com', **extra,
        )
        Cita.objects.create(
            negocio=self.negocio, cliente=cliente, servicio=servicio or self.corte,
            fecha_hora=timezone.now() - timedelta(days=hace_dias), duracion_minutos=30,
            estado='completada',
        )
        return cliente

    def _estado(self, cliente):
        s = next((s for s in seguimientos(self.negocio) if s.cliente.id == cliente.id), None)
        if s is None:
            return None
        return ('recuperar' if s.por_recuperar else '') + ('+recordar' if s.toca_recordatorio else '')

    def test_umbrales_con_frecuencia_de_30_dias(self, *mocks):
        self.assertEqual(self._estado(self._cliente_con_visita(31)), '')
        self.assertEqual(self._estado(self._cliente_con_visita(32)), '+recordar')
        self.assertEqual(self._estado(self._cliente_con_visita(44)), '+recordar')
        self.assertEqual(self._estado(self._cliente_con_visita(45)), 'recuperar+recordar')

    def test_umbrales_dependen_de_la_frecuencia_de_cada_servicio(self, *mocks):
        # Servicio cada 20 días: recordatorio a los 22, por recuperar a los 30
        cada_20 = Servicio.objects.create(
            negocio=self.negocio, nombre='Cejas', precio=15000, duracion_minutos=30, frecuencia_dias=20
        )
        self.assertEqual(self._estado(self._cliente_con_visita(21, cada_20)), '')
        self.assertEqual(self._estado(self._cliente_con_visita(22, cada_20)), '+recordar')
        self.assertEqual(self._estado(self._cliente_con_visita(29, cada_20)), '+recordar')
        self.assertEqual(self._estado(self._cliente_con_visita(30, cada_20)), 'recuperar+recordar')

    def test_servicio_sin_frecuencia(self, *mocks):
        self.assertEqual(self._estado(self._cliente_con_visita(60, self.sin_frecuencia)), '')
        self.assertEqual(self._estado(self._cliente_con_visita(90, self.sin_frecuencia)), 'recuperar')

    def test_con_cita_proxima_no_aplica(self, *mocks):
        cliente = self._cliente_con_visita(50)
        Cita.objects.create(
            negocio=self.negocio, cliente=cliente, servicio=self.corte,
            fecha_hora=timezone.now() + timedelta(days=2), duracion_minutos=30, estado='confirmada',
        )
        self.assertIsNone(self._estado(cliente))

    def test_cuenta_la_ultima_visita(self, *mocks):
        cliente = self._cliente_con_visita(60)
        Cita.objects.create(
            negocio=self.negocio, cliente=cliente, servicio=self.corte,
            fecha_hora=timezone.now() - timedelta(days=5), duracion_minutos=30, estado='completada',
        )
        self.assertEqual(self._estado(cliente), '')

    @patch.object(Notificacion, 'enviar', return_value={'success': True})
    def test_recordatorio_una_vez_por_ausencia(self, *mocks):
        a_tiempo = self._cliente_con_visita(32)
        temprano = self._cliente_con_visita(25)
        sin_promos = self._cliente_con_visita(40, acepta_promociones=False)

        sugerir_proximas_citas()
        sugerir_proximas_citas()  # al día siguiente: no se repite

        recordados = list(Notificacion.objects.filter(tipo='sugerencia_cita').values_list('cliente_id', flat=True))
        self.assertEqual(recordados, [a_tiempo.id])
        notif = Notificacion.objects.get(cliente=a_tiempo)
        self.assertIn('Han pasado 32 días', notif.mensaje)
        self.assertIn('/agendar/', notif.mensaje)
        self.assertNotIn(temprano.id, recordados)
        self.assertNotIn(sin_promos.id, recordados)

    @patch.object(Notificacion, 'enviar', return_value={'success': True})
    def test_nueva_ausencia_permite_otro_recordatorio(self, *mocks):
        cliente = self._cliente_con_visita(80)
        Notificacion.objects.create(
            cliente=cliente, tipo='sugerencia_cita', canal='email', asunto='x', mensaje='x'
        )
        Notificacion.objects.filter(cliente=cliente).update(fecha_creacion=timezone.now() - timedelta(days=45))
        # Volvió hace 33 días: es una ausencia nueva
        Cita.objects.create(
            negocio=self.negocio, cliente=cliente, servicio=self.corte,
            fecha_hora=timezone.now() - timedelta(days=33), duracion_minutos=30, estado='completada',
        )
        sugerir_proximas_citas()
        self.assertEqual(Notificacion.objects.filter(cliente=cliente, tipo='sugerencia_cita').count(), 2)

    @patch('apps.notificaciones.services.NotificacionService.enviar_push', return_value={'success': True})
    def test_push_lleva_a_agendar(self, enviar_push, *mocks):
        from apps.notificaciones.models import ClientePushSubscription
        cliente = self._cliente_con_visita(32)
        ClientePushSubscription.objects.create(cliente=cliente, endpoint='https://push/x', auth='a', p256dh='p')
        sugerir_proximas_citas()
        args, kwargs = enviar_push.call_args
        self.assertEqual(args[1], 'Spa')
        self.assertEqual(args[2], '¿Te agendamos tu próximo Corte?')
        self.assertEqual(kwargs['url'], f'/{self.negocio.slug}/agendar/')

    def test_lista_del_panel(self, *mocks):
        recuperar = self._cliente_con_visita(50)
        self._cliente_con_visita(10)
        self.assertEqual([s.cliente.id for s in clientes_por_recuperar(self.negocio)], [recuperar.id])

        self.client.force_login(self.admin)
        resp = self.client.get(reverse('public:admin_clientes_recuperar', args=[self.negocio.slug]))
        self.assertContains(resp, recuperar.nombre)
        self.assertContains(resp, '50 días sin venir')
        self.assertContains(resp, 'https://wa.me/57')
        resp = self.client.get(reverse('public:admin_clientes', args=[self.negocio.slug]))
        self.assertContains(resp, 'Clientes por recuperar')

    def test_segmento_de_promociones(self, *mocks):
        from apps.promociones.models import Promocion
        recuperar = self._cliente_con_visita(50)
        self._cliente_con_visita(10)
        promo = Promocion(negocio=self.negocio, segmento='inactivos')
        self.assertEqual(list(promo.obtener_clientes_segmento().values_list('id', flat=True)), [recuperar.id])

    def test_tarea_de_los_lunes_eliminada(self, *mocks):
        from config.celery import app
        self.assertNotIn('identificar-clientes-inactivos', app.conf.beat_schedule)
