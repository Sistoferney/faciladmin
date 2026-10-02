"""
Tests de abonos: al vencer, el dueño decide si confirma el pago o cancela la cita
"""
import tempfile
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings
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


@patch('apps.citas.signals.enviar_confirmacion_cita', create=True)
@patch('apps.notificaciones.models.Notificacion.enviar', return_value={'success': True})
class ConfirmarSinAbonoTests(TestCase):
    """
    Excepciones del dueño: confirmar una cita sin abono, y clientes de
    confianza a los que nunca se les pide.
    """

    def setUp(self):
        self.admin = Usuario.objects.create_user(
            telefono='3000000000', password='x', nombre='Admin', email='a@a.com'
        )
        self.negocio = Negocio.objects.create(
            administrador=self.admin, nombre='Spa', telefono='3000000000', banco='Banco Prueba'
        )
        self.servicio = Servicio.objects.create(
            negocio=self.negocio, nombre='Masaje', precio=50000, duracion_minutos=60,
            requiere_abono=True, monto_abono=20000,
        )
        self.cliente = Cliente.objects.create(
            negocio=self.negocio, nombre='Ana', telefono='3001111111', email='ana@correo.com'
        )
        self.cita = Cita.objects.create(
            negocio=self.negocio, cliente=self.cliente, servicio=self.servicio,
            fecha_hora=timezone.now() + timedelta(days=4), duracion_minutos=60,
            estado='pendiente_abono',
        )
        self.abono = Abono.objects.create(
            cita=self.cita, monto=20000, metodo_pago='transferencia', estado='pendiente',
            fecha_limite=timezone.now() + timedelta(days=2),
        )
        self.client.force_login(self.admin)
        self.url = reverse('public:cita_confirmar', args=[self.negocio.slug, self.cita.id])

    def _post(self, url, datos):
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(url, datos)

    def test_pantalla_ofrece_las_dos_opciones(self, *mocks):
        resp = self.client.get(self.url)
        self.assertContains(resp, 'Confirmar pago')
        self.assertContains(resp, 'Confirmar sin abono')

    def test_confirmar_sin_abono(self, *mocks):
        from apps.notificaciones.models import Notificacion
        self._post(self.url, {'modo': 'sin_abono', 'nota': 'Clienta frecuente'})

        self.abono.refresh_from_db()
        self.cita.refresh_from_db()
        self.cliente.refresh_from_db()
        self.assertEqual(self.abono.estado, 'exonerado')
        self.assertEqual(self.abono.notas_admin, 'Clienta frecuente')
        self.assertEqual(self.cita.estado, 'confirmada')
        self.assertFalse(self.cliente.no_exigir_abono)
        # Al cliente se le avisa que está confirmada (no que su pago fue confirmado)
        self.assertTrue(Notificacion.objects.filter(cita=self.cita, tipo='confirmacion_cita').exists())
        self.assertFalse(Notificacion.objects.filter(cita=self.cita, tipo='confirmacion_abono').exists())

    @patch('apps.notificaciones.services.NotificacionService.enviar_push')
    def test_exonerado_no_recibe_recordatorios_ni_se_vence(self, enviar_push, *mocks):
        self._post(self.url, {'modo': 'sin_abono'})
        Abono.objects.filter(pk=self.abono.pk).update(fecha_limite=timezone.now() - timedelta(hours=1))

        with patch('apps.notificaciones.tasks.enviar_recordatorio_abono.delay') as recordatorio:
            verificar_abonos_pendientes()

        recordatorio.assert_not_called()
        enviar_push.assert_not_called()  # sin aviso de "abono vencido" al dueño
        self.abono.refresh_from_db()
        self.assertEqual(self.abono.estado, 'exonerado')

    def test_no_volver_a_pedir_marca_al_cliente(self, *mocks):
        self._post(self.url, {'modo': 'sin_abono', 'no_exigir_mas': '1'})
        self.cliente.refresh_from_db()
        self.assertTrue(self.cliente.no_exigir_abono)

    def test_confirmar_pago(self, *mocks):
        from apps.notificaciones.models import Notificacion
        self._post(self.url, {'modo': 'pago'})
        self.abono.refresh_from_db()
        self.assertEqual(self.abono.estado, 'confirmado')
        self.assertEqual(self.abono.confirmado_por, self.admin)
        self.assertTrue(Notificacion.objects.filter(cita=self.cita, tipo='confirmacion_abono').exists())

    def test_interruptor_en_clientes(self, *mocks):
        url = reverse('public:cliente_no_exigir_abono', args=[self.negocio.slug, self.cliente.id])
        self.client.post(url)
        self.cliente.refresh_from_db()
        self.assertTrue(self.cliente.no_exigir_abono)
        resp = self.client.get(reverse('public:admin_clientes', args=[self.negocio.slug]))
        self.assertContains(resp, 'Pedir abono')
        self.client.post(url)
        self.cliente.refresh_from_db()
        self.assertFalse(self.cliente.no_exigir_abono)

    def test_otro_negocio_no_puede_cambiar_el_cliente(self, *mocks):
        otro = Usuario.objects.create_user(telefono='3009999999', password='x', nombre='Otro', email='o@o.com')
        Negocio.objects.create(administrador=otro, nombre='Otro Spa', telefono='3009999999')
        self.client.force_login(otro)
        self.client.post(reverse('public:cliente_no_exigir_abono', args=[self.negocio.slug, self.cliente.id]))
        self.cliente.refresh_from_db()
        self.assertFalse(self.cliente.no_exigir_abono)

    def test_cliente_de_confianza_agenda_sin_abono(self, *mocks):
        from apps.negocios.disponibilidad import horarios_disponibles
        self.cliente.no_exigir_abono = True
        self.cliente.save()
        self.client.logout()

        fecha = timezone.localdate() + timedelta(days=5)
        hora = horarios_disponibles(self.negocio, fecha, 60)[0]
        resp = self.client.post(reverse('public:agendar', args=[self.negocio.slug]), {
            'telefono': '300 111 1111', 'servicio': self.servicio.id,
            'fecha': fecha.isoformat(), 'hora': hora,
        })

        cita = Cita.objects.exclude(pk=self.cita.pk).get(cliente=self.cliente)
        self.assertEqual(cita.estado, 'confirmada')
        self.assertFalse(Abono.objects.filter(cita=cita).exists())
        # La confirmación no le muestra datos bancarios
        resp = self.client.get(resp.url)
        self.assertNotContains(resp, 'Banco Prueba')

    def test_cliente_normal_sigue_con_abono(self, *mocks):
        from apps.negocios.disponibilidad import horarios_disponibles
        self.client.logout()
        fecha = timezone.localdate() + timedelta(days=5)
        hora = horarios_disponibles(self.negocio, fecha, 60)[0]
        self.client.post(reverse('public:agendar', args=[self.negocio.slug]), {
            'telefono': '3001111111', 'servicio': self.servicio.id,
            'fecha': fecha.isoformat(), 'hora': hora,
        })
        cita = Cita.objects.exclude(pk=self.cita.pk).get(cliente=self.cliente)
        self.assertEqual(cita.estado, 'pendiente_abono')
        self.assertTrue(Abono.objects.filter(cita=cita).exists())


def _imagen(nombre='comprobante.png', tamano=(10, 10)):
    from io import BytesIO
    from PIL import Image
    from django.core.files.uploadedfile import SimpleUploadedFile
    buffer = BytesIO()
    Image.new('RGB', tamano, 'white').save(buffer, 'PNG')
    return SimpleUploadedFile(nombre, buffer.getvalue(), content_type='image/png')


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
@patch('apps.citas.signals.enviar_confirmacion_cita', create=True)
class PagoYComprobanteTests(TestCase):
    """
    El cliente ve los medios de pago del negocio, y envía el comprobante
    desde la app; el dueño lo revisa en Abonos.
    """

    def setUp(self):
        self.admin = Usuario.objects.create_user(
            telefono='3000000000', password='x', nombre='Admin', email='a@a.com'
        )
        self.negocio = Negocio.objects.create(
            administrador=self.admin, nombre='Spa', telefono='3000000000',
            nequi='3001112233', llave_breb='@spa', banco='Bancolombia', numero_cuenta='123456789',
            whatsapp='3009998888',
        )
        servicio = Servicio.objects.create(
            negocio=self.negocio, nombre='Masaje', precio=50000, duracion_minutos=60,
            requiere_abono=True, monto_abono=20000,
        )
        self.cliente = Cliente.objects.create(negocio=self.negocio, nombre='Ana', telefono='3001111111')
        self.cita = Cita.objects.create(
            negocio=self.negocio, cliente=self.cliente, servicio=servicio,
            fecha_hora=timezone.now() + timedelta(days=4), duracion_minutos=60,
            estado='pendiente_abono',
        )
        self.abono = Abono.objects.create(
            cita=self.cita, monto=20000, metodo_pago='transferencia', estado='pendiente',
            fecha_limite=timezone.now() + timedelta(days=2),
        )
        self.url_subir = reverse('public:subir_comprobante', args=[self.negocio.slug, self.cita.id])

    def _identificar_cliente(self):
        session = self.client.session
        session['clientes_verificados'] = {str(self.negocio.id): self.cliente.id}
        session.save()

    def test_confirmacion_muestra_medios_de_pago(self, *mocks):
        self._identificar_cliente()
        resp = self.client.get(reverse('public:confirmacion_cita', args=[self.negocio.slug, self.cita.id]))
        self.assertContains(resp, 'Nequi:')
        self.assertContains(resp, 'data-copiar="3001112233"')
        self.assertContains(resp, 'Llave Bre-B:')
        self.assertContains(resp, 'data-copiar="123456789"')
        self.assertContains(resp, 'Enviar comprobante')
        self.assertContains(resp, 'https://wa.me/573009998888?text=')
        self.assertNotContains(resp, 'CLABE')
        self.assertNotContains(resp, 'Daviplata:')  # no configurado

    def test_mis_citas_muestra_bloque_de_pago(self, *mocks):
        self._identificar_cliente()
        resp = self.client.get(reverse('public:mis_citas', args=[self.negocio.slug]))
        self.assertContains(resp, 'Paga tu abono para confirmar la cita')

    @patch('apps.notificaciones.services.NotificacionService.enviar_push', return_value={'success': True})
    def test_subir_comprobante(self, enviar_push, *mocks):
        self._identificar_cliente()
        with self.captureOnCommitCallbacks(execute=True):
            resp = self.client.post(self.url_subir, {
                'comprobante': _imagen(), 'numero_referencia': 'M12345',
            })
        self.assertRedirects(resp, reverse('public:mis_citas', args=[self.negocio.slug]))
        self.abono.refresh_from_db()
        self.assertTrue(self.abono.comprobante)
        self.assertEqual(self.abono.numero_referencia, 'M12345')
        self.assertIsNotNone(self.abono.fecha_pago)
        # Aviso al dueño que lo lleva a Abonos
        kwargs = enviar_push.call_args.kwargs
        self.assertTrue(kwargs['enviar_a_admin'])
        self.assertEqual(kwargs['url'], f'/{self.negocio.slug}/admin/abonos/')

        # Mis citas ahora indica que está en revisión
        resp = self.client.get(reverse('public:mis_citas', args=[self.negocio.slug]))
        self.assertContains(resp, 'Comprobante enviado')

        # El dueño lo ve en Abonos
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('public:abonos_admin', args=[self.negocio.slug]))
        self.assertContains(resp, 'Ver comprobante')

    def test_sin_identificarse_no_puede_subir(self, *mocks):
        self.client.post(self.url_subir, {'comprobante': _imagen()})
        self.abono.refresh_from_db()
        self.assertFalse(self.abono.comprobante)

    def test_rechaza_archivo_que_no_es_imagen(self, *mocks):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self._identificar_cliente()
        falso = SimpleUploadedFile('comprobante.png', b'no soy una imagen', content_type='image/png')
        self.client.post(self.url_subir, {'comprobante': falso})
        self.abono.refresh_from_db()
        self.assertFalse(self.abono.comprobante)

    @patch('apps.notificaciones.services.NotificacionService.enviar_push', return_value={'success': True})
    def test_nuevo_comprobante_tras_rechazo_vuelve_a_revision(self, *mocks):
        self.abono.estado = 'rechazado'
        self.abono.notas_admin = 'No se ve el monto'
        self.abono.save()
        self._identificar_cliente()
        resp = self.client.get(reverse('public:mis_citas', args=[self.negocio.slug]))
        self.assertContains(resp, 'No pudimos validar tu pago')
        self.assertContains(resp, 'No se ve el monto')

        self.client.post(self.url_subir, {'comprobante': _imagen()})
        self.abono.refresh_from_db()
        self.assertEqual(self.abono.estado, 'pendiente')

    def test_abono_ya_confirmado_no_acepta_comprobante(self, *mocks):
        self.abono.estado = 'confirmado'
        self.abono.save()
        self._identificar_cliente()
        self.client.post(self.url_subir, {'comprobante': _imagen()})
        self.abono.refresh_from_db()
        self.assertFalse(self.abono.comprobante)

    def test_texto_medios_pago_en_mensajes(self, *mocks):
        texto = self.negocio.texto_medios_pago()
        self.assertIn('Nequi: 3001112233', texto)
        self.assertIn('Llave Bre-B: @spa', texto)
        self.assertIn('Bancolombia: 123456789', texto)
        self.assertNotIn('Daviplata', texto)

    def test_whatsapp_comprobante_con_monto(self, *mocks):
        from urllib.parse import unquote
        from apps.core.whatsapp import enlace_comprobante
        enlace = unquote(enlace_comprobante(self.cita))
        self.assertIn('Hola Spa, te envío el comprobante del abono de $20.000', enlace)

    def test_configuracion_muestra_medios_aunque_negocio_no_exija_abono(self, *mocks):
        # El servicio pide abono, aunque el negocio no lo pida en general
        self.assertFalse(self.negocio.requiere_abono)
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('public:admin_configuracion', args=[self.negocio.slug]))
        self.assertContains(resp, 'id="mediosPago"')
        self.assertContains(resp, 'name="nequi"')
        self.assertContains(resp, 'name="qr_pago"')
