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

    # Las sugerencias (frecuencia + 2 días) se prueban en apps/fidelizacion/tests.py


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

    def test_admin_va_a_pendientes(self, webpush, *mocks):
        cita = self._cita(2)
        self.assertTrue(self._enviar(cita, a_admin=True)['success'])
        payload = self._payload(webpush)
        self.assertEqual(payload['url'], f'/{self.negocio.slug}/admin/pendientes/')
        self.assertEqual(payload['tag'], f'dueno-cita-{cita.id}')

    def test_cliente_va_a_mis_citas(self, webpush, *mocks):
        cita = self._cita(2)
        self._enviar(cita, a_admin=False)
        self.assertEqual(self._payload(webpush)['url'], f'/{self.negocio.slug}/mis-citas/')
        # Distinto del tag del dueño: un aviso no reemplaza al otro
        self.assertEqual(self._payload(webpush)['tag'], f'cita-{cita.id}')

    def test_citas_distintas_tienen_tags_distintos(self, webpush, *mocks):
        self._enviar(self._cita(2), a_admin=True)
        tag1 = self._payload(webpush)['tag']
        self._enviar(self._cita(3), a_admin=True)
        self.assertNotEqual(tag1, self._payload(webpush)['tag'])

    def test_sin_cita_no_hay_tag(self, webpush, *mocks):
        self._enviar(None, a_admin=False)
        self.assertNotIn('tag', self._payload(webpush))


class EnlaceWhatsappTests(TestCase):

    def test_agrega_codigo_de_pais(self):
        from apps.core.whatsapp import enlace_whatsapp
        # Antes: wa.me/3001234567 (sin 57) abría un número equivocado
        self.assertEqual(enlace_whatsapp('300 123 4567'), 'https://wa.me/573001234567')
        self.assertEqual(enlace_whatsapp('+57 300-123-4567'), 'https://wa.me/573001234567')

    def test_mensaje_prellenado(self):
        from apps.core.whatsapp import enlace_whatsapp
        self.assertEqual(
            enlace_whatsapp('3001234567', 'Hola, una duda'),
            'https://wa.me/573001234567?text=Hola%2C%20una%20duda',
        )

    def test_numero_invalido(self):
        from apps.core.whatsapp import enlace_whatsapp
        self.assertEqual(enlace_whatsapp(''), '')
        self.assertEqual(enlace_whatsapp('123'), '')


@patch('apps.citas.signals.enviar_confirmacion_cita', create=True)
@override_settings(TWILIO_ACCOUNT_SID='', TWILIO_AUTH_TOKEN='')
class AccionesPanelNotificanClienteTests(TestCase):
    """
    Lo que hace el dueño en el panel se le avisa al cliente, con enlace para
    resolver dudas por WhatsApp.
    """

    def setUp(self):
        from django.urls import reverse
        from apps.abonos.models import Abono
        self.reverse = reverse
        self.negocio, self.servicio, self.cliente = _crear_base()
        self.negocio.whatsapp = '300 999 8888'
        self.negocio.save()
        self.cita = Cita.objects.create(
            negocio=self.negocio, cliente=self.cliente, servicio=self.servicio,
            fecha_hora=_local(timezone.localdate() + timedelta(days=3), 10),
            duracion_minutos=30, estado='pendiente_abono',
        )
        self.abono = Abono.objects.create(
            cita=self.cita, monto=5000, metodo_pago='transferencia', estado='pendiente',
            fecha_limite=timezone.now() + timedelta(days=1),
        )
        self.client.force_login(self.negocio.administrador)

    def _post(self, nombre, obj_id, **datos):
        url = self.reverse(f'public:{nombre}', args=[self.negocio.slug, obj_id])
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(url, datos)

    @patch('apps.notificaciones.services.NotificacionService.enviar_email',
           return_value={'success': True})
    def test_cancelar_avisa_al_cliente_con_motivo_y_whatsapp(self, enviar_email, *mocks):
        self._post('cita_cancelar', self.cita.id, motivo='Cerramos por mantenimiento')

        notif = Notificacion.objects.get(cita=self.cita, tipo='cancelacion')
        self.assertIn('Cerramos por mantenimiento', notif.mensaje)
        enviado = enviar_email.call_args.args[2]
        self.assertIn('https://wa.me/573009998888?text=', enviado)

    @patch('apps.notificaciones.services.NotificacionService.enviar_email',
           return_value={'success': True})
    def test_confirmar_cita_avisa(self, *mocks):
        self._post('cita_confirmar', self.cita.id, modo='sin_abono')
        self.assertTrue(Notificacion.objects.filter(cita=self.cita, tipo='confirmacion_cita').exists())

    @patch('apps.notificaciones.services.NotificacionService.enviar_email',
           return_value={'success': True})
    def test_confirmar_abono_avisa(self, *mocks):
        self._post('abono_confirmar', self.abono.id)
        self.assertTrue(Notificacion.objects.filter(cita=self.cita, tipo='confirmacion_abono').exists())

    @patch('apps.notificaciones.services.NotificacionService.enviar_email',
           return_value={'success': True})
    def test_rechazar_abono_avisa_y_no_cancela_la_cita(self, *mocks):
        self._post('abono_rechazar', self.abono.id, motivo='El comprobante no es legible')
        notif = Notificacion.objects.get(cita=self.cita, tipo='abono_rechazado')
        self.assertIn('El comprobante no es legible', notif.mensaje)
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.estado, 'pendiente_abono')

    def test_fallo_al_notificar_no_rompe_la_accion(self, *mocks):
        with patch('apps.notificaciones.models.Notificacion.enviar', side_effect=RuntimeError('fallo')):
            self._post('cita_cancelar', self.cita.id)
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.estado, 'cancelada')


@patch('apps.citas.signals.enviar_confirmacion_cita', create=True)
@patch('py_vapid.Vapid.from_pem')
@patch('pywebpush.webpush')
class BotonWhatsappEnPushTests(TestCase):

    def setUp(self):
        from .models import UsuarioPushSubscription
        self.negocio, self.servicio, self.cliente = _crear_base()
        self.negocio.whatsapp = '3009998888'
        self.negocio.save()
        UsuarioPushSubscription.objects.create(
            user=self.negocio.administrador, negocio=self.negocio,
            endpoint='https://push/admin', auth='a', p256dh='p',
        )
        ClientePushSubscription.objects.create(
            cliente=self.cliente, endpoint='https://push/cliente', auth='a', p256dh='p'
        )
        self.cita = Cita.objects.create(
            negocio=self.negocio, cliente=self.cliente, servicio=self.servicio,
            fecha_hora=_local(timezone.localdate() + timedelta(days=2), 10),
            duracion_minutos=30, estado='confirmada',
        )

    def _payload(self, webpush, a_admin):
        import json
        from .services import NotificacionService
        NotificacionService().enviar_push(self.cliente, 'T', 'M', cita=self.cita, enviar_a_admin=a_admin)
        return json.loads(webpush.call_args.kwargs['data'])

    def test_dueno_recibe_boton_para_escribir_al_cliente(self, webpush, *mocks):
        payload = self._payload(webpush, a_admin=True)
        self.assertTrue(payload['whatsapp'].startswith('https://wa.me/573001111111?text=Hola%20Ana'))
        self.assertEqual(payload['actions'][0]['action'], 'whatsapp')

    def test_cliente_recibe_boton_para_escribir_al_negocio(self, webpush, *mocks):
        payload = self._payload(webpush, a_admin=False)
        self.assertTrue(payload['whatsapp'].startswith('https://wa.me/573009998888?text='))


class EnvioDeTareasTests(TestCase):
    """
    Las tareas deben usar la app de Celery del proyecto también en el servidor
    web (config/__init__.py). Si no, .delay() usa localhost y falla.
    """

    def test_tareas_usan_la_configuracion_del_proyecto(self):
        from django.conf import settings
        from .tasks import enviar_confirmacion_cita
        self.assertEqual(enviar_confirmacion_cita.app.main, 'faciladmin')
        self.assertEqual(enviar_confirmacion_cita.app.conf.broker_url, settings.CELERY_BROKER_URL)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=False)
    def test_si_redis_falla_se_envia_directamente(self):
        from unittest.mock import MagicMock
        from .tasks import programar_notificacion
        tarea = MagicMock(name='tarea')
        tarea.name = 'tarea_prueba'
        tarea.delay.side_effect = ConnectionRefusedError('Connection refused')

        with self.captureOnCommitCallbacks(execute=True):
            programar_notificacion(tarea, 123)

        tarea.delay.assert_called_once_with(123)
        tarea.assert_called_once_with(123)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=False)
    def test_con_redis_disponible_solo_se_encola(self):
        from unittest.mock import MagicMock
        from .tasks import programar_notificacion
        tarea = MagicMock(name='tarea')
        tarea.name = 'tarea_prueba'

        with self.captureOnCommitCallbacks(execute=True):
            programar_notificacion(tarea, 123)

        tarea.delay.assert_called_once_with(123)
        tarea.assert_not_called()


@patch('apps.citas.signals.enviar_confirmacion_cita', create=True)
@patch('py_vapid.Vapid.from_pem')
class SuscripcionClaveVapidAnteriorTests(TestCase):
    """
    Suscripciones creadas con otra clave VAPID responden 403 para siempre:
    se desactivan para dejar de intentarlo (el navegador se resuscribe solo).
    """

    def test_403_por_clave_vapid_desactiva_la_suscripcion(self, *mocks):
        from unittest.mock import MagicMock
        from pywebpush import WebPushException
        from .models import UsuarioPushSubscription
        from .services import NotificacionService

        negocio, servicio, cliente = _crear_base()
        sub = UsuarioPushSubscription.objects.create(
            user=negocio.administrador, negocio=negocio,
            endpoint='https://push/admin', auth='a', p256dh='p',
        )
        cita = Cita.objects.create(
            negocio=negocio, cliente=cliente, servicio=servicio,
            fecha_hora=_local(timezone.localdate() + timedelta(days=2), 10),
            duracion_minutos=30, estado='confirmada',
        )
        respuesta = MagicMock(status_code=403, text='the VAPID credentials in the authorization header do not correspond')
        with patch('pywebpush.webpush', side_effect=WebPushException('Push failed: 403', response=respuesta)):
            resultado = NotificacionService().enviar_push(cliente, 'T', 'M', cita=cita, enviar_a_admin=True)

        self.assertFalse(resultado['success'])
        sub.refresh_from_db()
        self.assertFalse(sub.activa)

    def test_otro_403_no_desactiva(self, *mocks):
        from unittest.mock import MagicMock
        from pywebpush import WebPushException
        from .services import NotificacionService

        negocio, _, cliente = _crear_base()
        sub = ClientePushSubscription.objects.create(
            cliente=cliente, endpoint='https://push/c', auth='a', p256dh='p'
        )
        respuesta = MagicMock(status_code=403, text='rate limited')
        with patch('pywebpush.webpush', side_effect=WebPushException('403', response=respuesta)):
            NotificacionService().enviar_push(cliente, 'T', 'M')
        sub.refresh_from_db()
        self.assertTrue(sub.activa)


@patch('apps.citas.signals.enviar_confirmacion_cita', create=True)
@patch('py_vapid.Vapid.from_pem')
@patch('pywebpush.webpush')
class OpcionesEntregaPushTests(TestCase):

    def test_push_con_ttl_y_prioridad_alta(self, webpush, *mocks):
        from .services import NotificacionService
        _, _, cliente = _crear_base()
        ClientePushSubscription.objects.create(cliente=cliente, endpoint='https://push/c', auth='a', p256dh='p')
        NotificacionService().enviar_push(cliente, 'T', 'M')
        kwargs = webpush.call_args.kwargs
        # Con TTL 0 (valor por defecto) Google descartaba el mensaje si el celular estaba en reposo
        self.assertEqual(kwargs['ttl'], 86400)
        self.assertEqual(kwargs['headers'], {'Urgency': 'high'})


class TextosPushCortosTests(TestCase):
    """
    Chrome Android oculta como "posible spam" los push largos con emojis,
    teléfonos y precios: los push llevan una frase corta.
    """

    def setUp(self):
        self.negocio, self.servicio, self.cliente = _crear_base()
        self.cliente.nombre = 'Ana López'
        self.cliente.save()
        from datetime import date
        # sábado 3 de octubre de 2026, 1:30 p. m.
        self.cita = Cita.objects.create(
            negocio=self.negocio, cliente=self.cliente, servicio=self.servicio,
            fecha_hora=_local(date(2026, 10, 3), 13).replace(minute=30),
            duracion_minutos=30, estado='confirmada',
        )

    def test_fecha_corta_en_espanol(self):
        from .textos_push import fecha_corta
        self.assertEqual(fecha_corta(self.cita.fecha_hora), 'sáb 3 oct, 1:30 p. m.')
        self.assertEqual(fecha_corta(self.cita.fecha_hora, con_hora=False), 'sáb 3 oct')

    def test_aviso_al_dueno_sin_telefono_precio_ni_emojis(self):
        import re
        from .textos_push import (push_dueno_nueva_cita, push_dueno_cita_cancelada,
                                  push_dueno_abono_vencido, push_dueno_comprobante,
                                  push_dueno_cita_modificada)
        titulo, cuerpo = push_dueno_nueva_cita(self.cita)
        self.assertEqual(titulo, 'Nueva cita')
        self.assertEqual(cuerpo, 'Ana López · Corte · sáb 3 oct, 1:30 p. m.')
        for funcion in (push_dueno_nueva_cita, push_dueno_cita_cancelada, push_dueno_abono_vencido,
                        push_dueno_comprobante, push_dueno_cita_modificada):
            _, texto = funcion(self.cita)
            self.assertNotIn('3001111111', texto)
            self.assertNotIn('$', texto)
            self.assertIsNone(re.search('[\U0001F300-\U0001FAFF]', texto), texto)

    def test_push_al_cliente_corto(self):
        from .textos_push import push_cliente
        titulo, cuerpo = push_cliente('confirmacion_cita', self.cita, self.negocio)
        self.assertEqual(titulo, 'Spa')
        self.assertEqual(cuerpo, 'Tu cita de Corte está confirmada para el sáb 3 oct, 1:30 p. m.')

        self.cita.estado = 'pendiente_abono'
        _, cuerpo = push_cliente('confirmacion_cita', self.cita, self.negocio)
        self.assertIn('Recuerda pagar el abono', cuerpo)

        _, cuerpo = push_cliente('recordatorio_cita', self.cita, self.negocio)
        self.assertEqual(cuerpo, 'Te esperamos mañana a la 1:30 p. m. para tu Corte.')

    @patch('apps.notificaciones.services.NotificacionService.enviar_push', return_value={'success': True})
    def test_notificacion_push_usa_texto_corto_y_email_conserva_el_largo(self, enviar_push):
        notif = Notificacion.objects.create(
            cliente=self.cliente, cita=self.cita, tipo='confirmacion_cita', canal='push',
            asunto='Confirmación de cita - Spa', mensaje='¡Hola Ana!\n\n📅 Fecha...\n💰 Precio: $10000',
        )
        notif.enviar()
        args = enviar_push.call_args.args
        self.assertEqual(args[1], 'Spa')
        self.assertTrue(args[2].startswith('Tu cita de Corte está confirmada'))
        self.assertNotIn('$', args[2])
        # El mensaje completo queda guardado (y es el que va por email/SMS)
        notif.refresh_from_db()
        self.assertIn('Precio', notif.mensaje)


class DesactivarSuscripcionesAnterioresTests(TestCase):
    """
    Al renovar su suscripción, el dispositivo informa las que canceló y el
    servidor las desactiva (en ambas tablas), sin esperar a que Google las rechace.
    """
    SUB = {'endpoint': 'https://push/nueva', 'keys': {'auth': 'a', 'p256dh': 'p'}}

    def setUp(self):
        from .models import UsuarioPushSubscription
        self.negocio, _, self.cliente = _crear_base()
        self.vieja_dueno = UsuarioPushSubscription.objects.create(
            user=self.negocio.administrador, negocio=self.negocio,
            endpoint='https://push/vieja', auth='a', p256dh='p',
        )
        # El SW antiguo compartía la suscripción entre panel y mini-página
        self.vieja_cliente = ClientePushSubscription.objects.create(
            cliente=self.cliente, endpoint='https://push/vieja', auth='a', p256dh='p'
        )
        self.otra = ClientePushSubscription.objects.create(
            cliente=self.cliente, endpoint='https://push/otro-dispositivo', auth='a', p256dh='p'
        )

    def test_suscripcion_del_dueno_desactiva_las_anteriores(self):
        import json
        self.client.force_login(self.negocio.administrador)
        resp = self.client.post('/api/notificaciones/push/subscribe-admin/', json.dumps({
            'subscription': self.SUB, 'negocio_slug': self.negocio.slug,
            'endpoints_anteriores': ['https://push/vieja'],
        }), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        for sub in (self.vieja_dueno, self.vieja_cliente, self.otra):
            sub.refresh_from_db()
        self.assertFalse(self.vieja_dueno.activa)
        self.assertFalse(self.vieja_cliente.activa)
        self.assertTrue(self.otra.activa)  # otro dispositivo: no se toca

    def test_sin_anteriores_no_desactiva_nada(self):
        import json
        self.client.force_login(self.negocio.administrador)
        self.client.post('/api/notificaciones/push/subscribe-admin/', json.dumps({
            'subscription': self.SUB, 'negocio_slug': self.negocio.slug,
        }), content_type='application/json')
        self.vieja_dueno.refresh_from_db()
        self.assertTrue(self.vieja_dueno.activa)


@patch('apps.citas.signals.enviar_confirmacion_cita', create=True)
@override_settings(TWILIO_ACCOUNT_SID='', TWILIO_AUTH_TOKEN='')
class Recordatorio2HorasTests(TestCase):

    def setUp(self):
        self.negocio, self.servicio, self.cliente = _crear_base()

    def _cita(self, en_minutos, estado='confirmada', creada_hace_min=120):
        cita = Cita.objects.create(
            negocio=self.negocio, cliente=self.cliente, servicio=self.servicio,
            fecha_hora=timezone.now() + timedelta(minutes=en_minutos),
            duracion_minutos=30, estado=estado,
        )
        Cita.objects.filter(pk=cita.pk).update(fecha_creacion=timezone.now() - timedelta(minutes=creada_hace_min))
        return cita

    @patch.object(Notificacion, 'enviar', return_value={'success': True})
    def test_solo_citas_confirmadas_en_las_proximas_2_horas(self, *mocks):
        from .tasks import enviar_recordatorios_2h
        en_90 = self._cita(90)
        en_3h = self._cita(180)
        pendiente = self._cita(60, estado='pendiente_abono')
        recien = self._cita(60, creada_hace_min=10)  # acaba de recibir la confirmación

        enviar_recordatorios_2h()

        enviadas = set(Notificacion.objects.filter(tipo='recordatorio_2h').values_list('cita_id', flat=True))
        self.assertEqual(enviadas, {en_90.id})
        for c, esperado in [(en_90, True), (en_3h, False), (pendiente, False), (recien, False)]:
            c.refresh_from_db()
            self.assertEqual(c.recordatorio_2h_enviado, esperado)

    @patch.object(Notificacion, 'enviar', return_value={'success': True})
    def test_no_se_repite(self, *mocks):
        from .tasks import enviar_recordatorios_2h
        self._cita(90)
        enviar_recordatorios_2h()
        enviar_recordatorios_2h()
        self.assertEqual(Notificacion.objects.filter(tipo='recordatorio_2h').count(), 1)

    def test_texto_push(self, *mocks):
        from .textos_push import push_cliente
        from datetime import date
        cita = self._cita(90)
        cita.fecha_hora = _local(date(2026, 10, 3), 15)
        _, cuerpo = push_cliente('recordatorio_2h', cita, self.negocio)
        self.assertEqual(cuerpo, 'Tu cita de Corte es hoy a las 3:00 p. m. ¡Te esperamos!')
        cita.fecha_hora = _local(date(2026, 10, 3), 13)
        _, cuerpo = push_cliente('recordatorio_2h', cita, self.negocio)
        self.assertIn('es hoy a la 1:00 p. m.', cuerpo)

    def test_aviso_cita_hoy_en_mis_citas(self, *mocks):
        from django.urls import reverse
        cita = self._cita(60)
        if timezone.localtime(cita.fecha_hora).date() != timezone.localdate():
            self.skipTest('La cita de prueba cae mañana (se ejecuta cerca de medianoche)')
        session = self.client.session
        session['clientes_verificados'] = {str(self.negocio.id): self.cliente.id}
        session.save()
        resp = self.client.get(reverse('public:mis_citas', args=[self.negocio.slug]))
        self.assertContains(resp, 'Tu cita de Corte es hoy')

    def test_programada_cada_15_minutos(self, *mocks):
        from config.celery import app
        tarea = app.conf.beat_schedule['recordatorios-2h']
        self.assertEqual(tarea['task'], 'apps.notificaciones.tasks.enviar_recordatorios_2h')
        self.assertEqual(tarea['schedule'].minute, {0, 15, 30, 45})


@patch('apps.citas.signals.enviar_confirmacion_cita', create=True)
@override_settings(TWILIO_ACCOUNT_SID='', TWILIO_AUTH_TOKEN='')
class SinAvisosDeCitasPasadasTests(TestCase):
    """Cancelar o confirmar una cita que ya pasó no le avisa al cliente"""

    def setUp(self):
        from django.urls import reverse
        self.reverse = reverse
        self.negocio, self.servicio, self.cliente = _crear_base()
        self.client.force_login(self.negocio.administrador)

    def _cita(self, dias):
        return Cita.objects.create(
            negocio=self.negocio, cliente=self.cliente, servicio=self.servicio,
            fecha_hora=timezone.now() + timedelta(days=dias), duracion_minutos=30, estado='confirmada',
        )

    def _cancelar(self, cita):
        url = self.reverse('public:cita_cancelar', args=[self.negocio.slug, cita.id])
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(url, {'motivo': 'No vino'}, follow=True)

    @patch.object(Notificacion, 'enviar', return_value={'success': True})
    def test_cancelar_cita_vencida_no_avisa(self, *mocks):
        cita = self._cita(-20)
        resp = self._cancelar(cita)
        cita.refresh_from_db()
        self.assertEqual(cita.estado, 'cancelada')
        self.assertFalse(Notificacion.objects.filter(cita=cita).exists())
        self.assertNotContains(resp, 'Le avisaremos al cliente')

    @patch.object(Notificacion, 'enviar', return_value={'success': True})
    def test_cancelar_cita_futura_si_avisa(self, *mocks):
        cita = self._cita(3)
        resp = self._cancelar(cita)
        self.assertTrue(Notificacion.objects.filter(cita=cita, tipo='cancelacion').exists())
        self.assertContains(resp, 'Le avisaremos al cliente')

    @patch.object(Notificacion, 'enviar', return_value={'success': True})
    def test_tareas_ignoran_citas_pasadas(self, *mocks):
        from .tasks import notificar_cambio_cita, enviar_notificacion_confirmacion_abono
        cita = self._cita(-5)
        self.assertFalse(notificar_cambio_cita(cita.id, 'cancelada')['success'])
        self.assertFalse(enviar_notificacion_confirmacion_abono(cita.id)['success'])
        self.assertFalse(Notificacion.objects.filter(cita=cita).exists())


class _RespuestaPush:
    def __init__(self, status_code, text=''):
        self.status_code = status_code
        self.text = text


@patch('apps.citas.signals.enviar_confirmacion_cita', create=True)
@patch('py_vapid.Vapid.from_pem')
@patch('pywebpush.webpush')
class FallosConsecutivosPushTests(TestCase):
    """
    Una suscripción que el servicio de push rechaza 3 veces seguidas se
    desactiva; un envío exitoso reinicia la cuenta.
    """

    def setUp(self):
        _, _, self.cliente = _crear_base()
        self.sub = ClientePushSubscription.objects.create(
            cliente=self.cliente, endpoint='https://push/1', auth='a', p256dh='p'
        )

    def _enviar(self):
        from .services import NotificacionService
        return NotificacionService().enviar_push(self.cliente, 'Título', 'Mensaje')

    def _rechazo(self, status=500):
        from pywebpush import WebPushException
        return WebPushException('rechazado', response=_RespuestaPush(status))

    def test_tres_rechazos_seguidos_desactivan(self, webpush, *mocks):
        webpush.side_effect = self._rechazo()
        for esperado in (1, 2):
            self._enviar()
            self.sub.refresh_from_db()
            self.assertEqual(self.sub.fallos_consecutivos, esperado)
            self.assertTrue(self.sub.activa)
        self._enviar()
        self.sub.refresh_from_db()
        self.assertFalse(self.sub.activa)

    def test_exito_reinicia_la_cuenta(self, webpush, *mocks):
        webpush.side_effect = self._rechazo()
        self._enviar()
        self._enviar()
        webpush.side_effect = None
        self._enviar()
        self.sub.refresh_from_db()
        self.assertEqual(self.sub.fallos_consecutivos, 0)
        self.assertTrue(self.sub.activa)

    def test_error_propio_no_cuenta(self, webpush, *mocks):
        # Sin respuesta del servicio (sin red, clave mal configurada): no es culpa del dispositivo
        webpush.side_effect = RuntimeError('clave mal configurada')
        for _ in range(4):
            self._enviar()
        self.sub.refresh_from_db()
        self.assertEqual(self.sub.fallos_consecutivos, 0)
        self.assertTrue(self.sub.activa)

    def test_renovar_suscripcion_reinicia_la_cuenta(self, *mocks):
        self.sub.fallos_consecutivos = 3
        self.sub.activa = False
        self.sub.save()
        ClientePushSubscription.crear_desde_subscription_info(
            self.cliente, {'endpoint': 'https://push/1', 'keys': {'auth': 'a', 'p256dh': 'p'}}
        )
        self.sub.refresh_from_db()
        self.assertTrue(self.sub.activa)
        self.assertEqual(self.sub.fallos_consecutivos, 0)


@patch('apps.citas.signals.enviar_confirmacion_cita', create=True)
class LimpiezaHistorialTests(TestCase):

    def setUp(self):
        self.negocio, self.servicio, self.cliente = _crear_base()

    def _envejecer(self, modelo, obj, campo, dias):
        modelo.objects.filter(pk=obj.pk).update(**{campo: timezone.now() - timedelta(days=dias)})

    def test_borra_solo_lo_viejo_y_resuelto(self, *mocks):
        from .models import Pendiente
        from .tasks import limpiar_historial_notificaciones

        vieja = Notificacion.objects.create(cliente=self.cliente, tipo='recordatorio_cita', canal='email', mensaje='x')
        reciente = Notificacion.objects.create(cliente=self.cliente, tipo='recordatorio_cita', canal='email', mensaje='x')
        self._envejecer(Notificacion, vieja, 'fecha_creacion', 91)

        citas = [
            Cita.objects.create(
                negocio=self.negocio, cliente=self.cliente, servicio=self.servicio,
                fecha_hora=_local(timezone.localdate() + timedelta(days=d), 10), duracion_minutos=30,
            ) for d in (1, 2, 3)
        ]
        Pendiente.objects.all().delete()  # los que crean las señales al agendar
        resuelto_viejo, abierto_viejo, resuelto_reciente = [
            Pendiente.objects.create(negocio=self.negocio, cita=cita, tipo='cita_nueva', resuelto=resuelto)
            for cita, resuelto in zip(citas, (True, False, True))
        ]
        self._envejecer(Pendiente, resuelto_viejo, 'actualizado_en', 31)
        self._envejecer(Pendiente, abierto_viejo, 'actualizado_en', 200)

        inactiva = ClientePushSubscription.objects.create(
            cliente=self.cliente, endpoint='https://push/viejo', auth='a', p256dh='p', activa=False)
        activa = ClientePushSubscription.objects.create(
            cliente=self.cliente, endpoint='https://push/activo', auth='a', p256dh='p')
        self._envejecer(ClientePushSubscription, inactiva, 'fecha_actualizacion', 91)
        self._envejecer(ClientePushSubscription, activa, 'fecha_actualizacion', 300)

        limpiar_historial_notificaciones()

        self.assertEqual(list(Notificacion.objects.all()), [reciente])
        self.assertCountEqual(Pendiente.objects.all(), [abierto_viejo, resuelto_reciente])
        self.assertEqual(list(ClientePushSubscription.objects.all()), [activa])


class SuscripcionesCruzadasTests(TestCase):
    """
    El panel del dueño se suscribía con el Service Worker de la mini-página
    del mismo celular: los avisos del dueño llegaban a la app del cliente.
    """
    MINI = 'https://push/minipagina'
    PANEL = 'https://push/panel'

    def setUp(self):
        from .models import UsuarioPushSubscription
        self.negocio, _, self.cliente = _crear_base()
        session = self.client.session
        session['clientes_verificados'] = {str(self.negocio.id): self.cliente.id}
        session.save()
        # Estado dañado: la suscripción de la mini-página guardada también como del dueño
        ClientePushSubscription.objects.create(cliente=self.cliente, endpoint=self.MINI, auth='a', p256dh='p')
        self.cruzada = UsuarioPushSubscription.objects.create(
            user=self.negocio.administrador, negocio=self.negocio, endpoint=self.MINI, auth='a', p256dh='p'
        )

    def _post(self, url, endpoint, **extra):
        import json
        sub = {'endpoint': endpoint, 'keys': {'auth': 'a', 'p256dh': 'p'}}
        return self.client.post(url, json.dumps(
            {'subscription': sub, 'negocio_slug': self.negocio.slug, **extra}
        ), content_type='application/json')

    def test_minipagina_recupera_su_suscripcion(self):
        self._post('/api/notificaciones/push/subscribe/', self.MINI)
        self.cruzada.refresh_from_db()
        self.assertFalse(self.cruzada.activa)
        self.assertTrue(ClientePushSubscription.objects.get(endpoint=self.MINI).activa)

    def test_panel_reporta_la_suscripcion_de_la_minipagina(self):
        self.client.force_login(self.negocio.administrador)
        resp = self._post('/api/notificaciones/push/subscribe-admin/', self.PANEL, endpoints_otra_app=[self.MINI])
        self.assertEqual(resp.status_code, 200)
        self.cruzada.refresh_from_db()
        self.assertFalse(self.cruzada.activa)
        # La del cliente sigue activa: es suya
        self.assertTrue(ClientePushSubscription.objects.get(endpoint=self.MINI).activa)
