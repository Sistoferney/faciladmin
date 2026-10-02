"""
Tests de las tareas de notificaciones
"""
from datetime import datetime, timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from apps.authentication.models import Usuario
from apps.citas.models import Cita
from apps.clientes.models import Cliente
from apps.negocios.models import Negocio
from apps.servicios.models import Servicio

from .models import ClientePushSubscription, Notificacion
from .services import elegir_canal
from .tasks import enviar_confirmacion_cita


@patch('apps.citas.signals.enviar_confirmacion_cita', create=True)
class MensajesHoraLocalTests(TestCase):
    """
    Las fechas se guardan en UTC: los mensajes deben mostrar la hora de Colombia.
    """

    @patch('apps.notificaciones.services.NotificacionService')
    @patch.object(Notificacion, 'enviar', return_value={'success': True})
    def test_confirmacion_muestra_hora_local(self, *mocks):
        admin = Usuario.objects.create_user(
            telefono='3000000000', password='x', nombre='Admin', email='a@a.com'
        )
        negocio = Negocio.objects.create(
            administrador=admin, nombre='Spa Prueba', telefono='3000000000'
        )
        servicio = Servicio.objects.create(
            negocio=negocio, nombre='Corte', precio=10000, duracion_minutos=30
        )
        cliente = Cliente.objects.create(
            negocio=negocio, nombre='Ana', telefono='3001111111', email='ana@correo.com'
        )
        fecha = timezone.localdate() + timedelta(days=3)
        cita = Cita.objects.create(
            negocio=negocio, cliente=cliente, servicio=servicio,
            fecha_hora=timezone.make_aware(datetime.combine(fecha, datetime.min.time().replace(hour=9))),
            duracion_minutos=30, estado='confirmada',
        )

        enviar_confirmacion_cita(cita.id)

        mensaje = Notificacion.objects.get(cita=cita).mensaje
        self.assertIn('🕐 Hora: 09:00', mensaje)
        self.assertNotIn('14:00', mensaje)  # 09:00 Bogotá = 14:00 UTC


def _crear_base():
    admin = Usuario.objects.create_user(
        telefono='3000000000', password='x', nombre='Admin', email='a@a.com'
    )
    negocio = Negocio.objects.create(administrador=admin, nombre='Spa', telefono='3000000000')
    servicio = Servicio.objects.create(
        negocio=negocio, nombre='Corte', precio=10000, duracion_minutos=30, frecuencia_dias=30
    )
    cliente = Cliente.objects.create(
        negocio=negocio, nombre='Ana', telefono='3001111111', email='ana@correo.com'
    )
    return negocio, servicio, cliente


def _local(fecha, hora):
    return timezone.make_aware(datetime.combine(fecha, datetime.min.time().replace(hour=hora)))


@override_settings(TWILIO_ACCOUNT_SID='', TWILIO_AUTH_TOKEN='')
class ElegirCanalTests(TestCase):

    def setUp(self):
        _, _, self.cliente = _crear_base()

    def test_sin_twilio_no_elige_whatsapp(self):
        # acepta_whatsapp=True por defecto, pero sin Twilio fallaría siempre
        self.assertEqual(elegir_canal(self.cliente), 'email')

    def test_sin_canales_disponibles(self):
        self.cliente.email = ''
        self.assertIsNone(elegir_canal(self.cliente))

    def test_push_tiene_prioridad(self):
        ClientePushSubscription.objects.create(
            cliente=self.cliente, endpoint='https://push/1', auth='a', p256dh='p'
        )
        self.assertEqual(elegir_canal(self.cliente), 'push')

    @override_settings(TWILIO_ACCOUNT_SID='sid', TWILIO_AUTH_TOKEN='tok',
                       TWILIO_WHATSAPP_NUMBER='+1555')
    def test_con_twilio_usa_whatsapp(self):
        self.assertEqual(elegir_canal(self.cliente), 'whatsapp')


@patch('apps.citas.signals.enviar_confirmacion_cita', create=True)
@override_settings(TWILIO_ACCOUNT_SID='', TWILIO_AUTH_TOKEN='')
class TareasProgramadasTests(TestCase):

    def setUp(self):
        self.negocio, self.servicio, self.cliente = _crear_base()

    def _cita(self, fecha_hora, **extra):
        return Cita.objects.create(
            negocio=self.negocio, cliente=self.cliente, servicio=self.servicio,
            fecha_hora=fecha_hora, duracion_minutos=30,
            estado=extra.pop('estado', 'confirmada'), **extra
        )

    @patch.object(Notificacion, 'enviar', return_value={'success': True})
    def test_recordatorios_cubren_manana_en_hora_local(self, *mocks):
        from .tasks import enviar_recordatorios_citas
        manana = timezone.localdate() + timedelta(days=1)
        temprano = self._cita(_local(manana, 8))       # 13:00 UTC
        tarde = self._cita(_local(manana, 20))         # 01:00 UTC del día siguiente
        pasado = self._cita(_local(manana + timedelta(days=1), 2))

        enviar_recordatorios_citas()

        for cita, esperado in [(temprano, True), (tarde, True), (pasado, False)]:
            cita.refresh_from_db()
            self.assertEqual(cita.recordatorio_enviado, esperado, cita.fecha_hora)

    @patch('apps.notificaciones.services.NotificacionService.enviar_push',
           return_value={'success': True})
    def test_confirmacion_avisa_al_admin_aunque_cliente_no_tenga_canal(self, enviar_push, *mocks):
        self.cliente.email = ''
        self.cliente.save()
        cita = self._cita(_local(timezone.localdate() + timedelta(days=2), 10))

        enviar_confirmacion_cita(cita.id)

        self.assertFalse(Notificacion.objects.filter(cita=cita).exists())
        self.assertTrue(enviar_push.call_args.kwargs.get('enviar_a_admin'))

    def test_completar_desde_panel_actualiza_ultima_visita(self, *mocks):
        from django.urls import reverse
        cita = self._cita(_local(timezone.localdate() - timedelta(days=1), 10))
        self.client.force_login(self.negocio.administrador)
        self.client.post(reverse('public:cita_completar', args=[self.negocio.slug, cita.id]))
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.ultima_visita, cita.fecha_hora)
        self.assertEqual(self.cliente.total_citas, 1)

    @patch.object(Notificacion, 'enviar', return_value={'success': True})
    def test_sugerencia_ignora_citas_si_el_cliente_volvio(self, *mocks):
        from apps.fidelizacion.tasks import sugerir_proximas_citas
        hoy = timezone.localdate()
        self._cita(_local(hoy - timedelta(days=28), 10), estado='completada')
        self.cliente.acepta_promociones = True
        self.cliente.save()

        self._cita(_local(hoy - timedelta(days=2), 10), estado='completada')
        sugerir_proximas_citas()
        self.assertFalse(Notificacion.objects.filter(tipo='sugerencia_cita').exists())

    @patch.object(Notificacion, 'enviar', return_value={'success': True})
    def test_sugerencia_se_envia_cerca_de_la_frecuencia(self, *mocks):
        from apps.fidelizacion.tasks import sugerir_proximas_citas
        self._cita(_local(timezone.localdate() - timedelta(days=28), 10), estado='completada')
        self.cliente.acepta_promociones = True
        self.cliente.save()
        sugerir_proximas_citas()
        self.assertEqual(Notificacion.objects.filter(tipo='sugerencia_cita').count(), 1)


class SuscripcionPushClienteTests(TestCase):
    """
    La suscripción push del cliente usa la sesión, no un teléfono enviado
    por el navegador (en iPhone la app no comparte localStorage con Safari).
    """
    SUB = {'endpoint': 'https://push.example/abc', 'keys': {'auth': 'a', 'p256dh': 'p'}}

    def setUp(self):
        self.negocio, _, self.cliente = _crear_base()
        self.url = '/api/notificaciones/push/subscribe/'

    def _post(self, **extra):
        import json
        return self.client.post(
            self.url,
            json.dumps({'subscription': self.SUB, 'negocio_slug': self.negocio.slug, **extra}),
            content_type='application/json',
        )

    def test_sin_identificarse_pide_ir_a_mis_citas(self):
        resp = self._post()
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json()['codigo'], 'identificacion_requerida')
        self.assertFalse(ClientePushSubscription.objects.exists())

    def test_no_acepta_telefono_ajeno_sin_sesion(self):
        # Antes bastaba con enviar el teléfono de otra persona
        resp = self._post(telefono='3001111111')
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(ClientePushSubscription.objects.exists())

    def test_cliente_identificado_se_suscribe(self):
        session = self.client.session
        session['clientes_verificados'] = {str(self.negocio.id): self.cliente.id}
        session.save()
        resp = self._post()
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(ClientePushSubscription.objects.filter(
            cliente=self.cliente, endpoint=self.SUB['endpoint']).exists())

        # Reenviar la misma suscripción no la duplica
        self._post()
        self.assertEqual(ClientePushSubscription.objects.count(), 1)


@patch('apps.citas.signals.enviar_confirmacion_cita', create=True)
@patch('py_vapid.Vapid.from_pem')
@patch('pywebpush.webpush')
class PayloadPushTests(TestCase):
    """
    Cada cita tiene su propio tag (no se reemplazan notificaciones de citas
    distintas) y al tocarla cada quien va a su app: dueño a la agenda,
    cliente a sus citas.
    """

    def setUp(self):
        from .models import UsuarioPushSubscription
        self.negocio, self.servicio, self.cliente = _crear_base()
        UsuarioPushSubscription.objects.create(
            user=self.negocio.administrador, negocio=self.negocio,
            endpoint='https://push/admin', auth='a', p256dh='p',
        )
        ClientePushSubscription.objects.create(
            cliente=self.cliente, endpoint='https://push/cliente', auth='a', p256dh='p'
        )

    def _cita(self, dias):
        return Cita.objects.create(
            negocio=self.negocio, cliente=self.cliente, servicio=self.servicio,
            fecha_hora=_local(timezone.localdate() + timedelta(days=dias), 10),
            duracion_minutos=30, estado='confirmada',
        )

    def _payload(self, webpush):
        import json
        return json.loads(webpush.call_args.kwargs['data'])

    def _enviar(self, cita, a_admin):
        from .services import NotificacionService
        return NotificacionService().enviar_push(
            self.cliente, 'Título', 'Mensaje', cita=cita, enviar_a_admin=a_admin
        )

    def test_admin_va_a_la_agenda(self, webpush, *mocks):
        cita = self._cita(2)
        self.assertTrue(self._enviar(cita, a_admin=True)['success'])
        payload = self._payload(webpush)
        self.assertEqual(payload['url'], f'/{self.negocio.slug}/admin/agenda/')
        self.assertEqual(payload['tag'], f'cita-{cita.id}')

    def test_cliente_va_a_mis_citas(self, webpush, *mocks):
        self._enviar(self._cita(2), a_admin=False)
        self.assertEqual(self._payload(webpush)['url'], f'/{self.negocio.slug}/mis-citas/')

    def test_citas_distintas_tienen_tags_distintos(self, webpush, *mocks):
        self._enviar(self._cita(2), a_admin=True)
        tag1 = self._payload(webpush)['tag']
        self._enviar(self._cita(3), a_admin=True)
        self.assertNotEqual(tag1, self._payload(webpush)['tag'])

    def test_sin_cita_no_hay_tag(self, webpush, *mocks):
        self._enviar(None, a_admin=False)
        self.assertNotIn('tag', self._payload(webpush))
