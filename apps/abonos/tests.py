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


class FormatoPesosTests(TestCase):

    def test_pesos(self):
        from apps.core.formato import pesos
        self.assertEqual(pesos(20000), '$20.000')
        self.assertEqual(pesos(1500000), '$1.500.000')
        self.assertEqual(pesos(None), '')

    def test_parsear_monto(self):
        from decimal import Decimal
        from apps.core.formato import parsear_monto
        for texto in ['50.000', '$ 50.000', '50000', ' 50 000 ']:
            self.assertEqual(parsear_monto(texto), Decimal(50000), texto)
        self.assertIsNone(parsear_monto(''))
        self.assertIsNone(parsear_monto('abc'))


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
@patch('apps.citas.signals.enviar_confirmacion_cita', create=True)
@patch('apps.notificaciones.models.Notificacion.enviar', return_value={'success': True})
class MontoPagadoYSaldoTests(TestCase):
    """
    El cliente puede pagar más que el abono o el total; el dueño registra lo
    recibido y el sistema calcula lo que falta cobrar en el local.
    Servicio de $50.000 con abono exigido de $20.000.
    """

    def setUp(self):
        self.admin = Usuario.objects.create_user(
            telefono='3000000000', password='x', nombre='Admin', email='a@a.com'
        )
        self.negocio = Negocio.objects.create(administrador=self.admin, nombre='Spa', telefono='3000000000')
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

    def _confirmar(self, monto, desde='abonos'):
        if desde == 'abonos':
            url = reverse('public:abono_confirmar', args=[self.negocio.slug, self.abono.id])
            datos = {}
        else:
            url = reverse('public:cita_confirmar', args=[self.negocio.slug, self.cita.id])
            datos = {'modo': 'pago'}
        if monto is not None:
            datos['monto_pagado'] = monto
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(url, datos)
        self.cita = Cita.objects.get(pk=self.cita.pk)

    def test_pago_solo_del_abono(self, *mocks):
        self._confirmar('20.000')
        self.assertEqual(self.cita.monto_pagado, 20000)
        self.assertEqual(self.cita.saldo_pendiente, 30000)
        self.assertFalse(self.cita.pagado_completo)

    def test_pago_mayor_al_abono(self, *mocks):
        self._confirmar('$ 35.000', desde='agenda')
        self.assertEqual(self.cita.saldo_pendiente, 15000)

    def test_pago_total(self, *mocks):
        self._confirmar('50000')
        self.assertTrue(self.cita.pagado_completo)
        self.assertEqual(self.cita.saldo_pendiente, 0)

    def test_pago_mayor_al_precio_no_deja_saldo_negativo(self, *mocks):
        self._confirmar('55.000')  # propina
        self.assertEqual(self.cita.saldo_pendiente, 0)
        self.assertEqual(self.cita.monto_pagado, 55000)

    def test_sin_monto_usa_lo_reportado_por_el_cliente(self, *mocks):
        self.abono.monto_reportado = 50000
        self.abono.save()
        self._confirmar(None)
        self.assertTrue(self.cita.pagado_completo)

    def test_sin_monto_ni_reporte_usa_el_exigido(self, *mocks):
        self._confirmar(None)
        self.assertEqual(self.cita.monto_pagado, 20000)

    def test_abonos_confirmados_antes_del_cambio(self, *mocks):
        # Confirmados sin registrar monto_pagado: se asume el exigido
        Abono.objects.filter(pk=self.abono.pk).update(estado='confirmado', monto_pagado=None)
        cita = Cita.objects.get(pk=self.cita.pk)
        self.assertEqual(cita.monto_pagado, 20000)
        self.assertEqual(cita.saldo_pendiente, 30000)

    def test_exonerado_paga_todo_en_el_local(self, *mocks):
        self.abono.exonerar(self.admin)
        cita = Cita.objects.get(pk=self.cita.pk)
        self.assertEqual(cita.monto_pagado, 0)
        self.assertEqual(cita.saldo_pendiente, 50000)

    def test_saldo_se_recalcula_si_cambia_el_servicio(self, *mocks):
        self._confirmar('20000')
        otro = Servicio.objects.create(negocio=self.negocio, nombre='Facial', precio=80000, duracion_minutos=60)
        self.cita.servicio = otro
        self.cita.save()
        self.assertEqual(Cita.objects.get(pk=self.cita.pk).saldo_pendiente, 60000)

    def test_pantallas_del_dueno(self, *mocks):
        # Al confirmar: campo "¿Cuánto recibiste?" con botón para el total
        resp = self.client.get(reverse('public:abono_confirmar', args=[self.negocio.slug, self.abono.id]))
        self.assertContains(resp, '¿Cuánto recibiste?')
        self.assertContains(resp, "value='50000'")

        self._confirmar('20000')
        # Al completar la cita: cuánto cobrar
        resp = self.client.get(reverse('public:cita_completar', args=[self.negocio.slug, self.cita.id]))
        self.assertContains(resp, 'Cobra al cliente')
        self.assertContains(resp, '$30.000')
        # En Abonos: lo recibido y el saldo
        resp = self.client.get(reverse('public:abonos_admin', args=[self.negocio.slug]) + '?estado=todos')
        self.assertContains(resp, 'Saldo: $30.000')

    def test_agenda_muestra_resumen_de_pago(self, *mocks):
        self._confirmar('20000')
        fecha = timezone.localtime(self.cita.fecha_hora).date()
        resp = self.client.get(reverse('public:admin_agenda', args=[self.negocio.slug]), {'fecha': fecha.isoformat()})
        self.assertContains(resp, 'Saldo por cobrar: $30.000')

    def test_mensaje_al_cliente_con_saldo(self, *mocks):
        from apps.notificaciones.models import Notificacion
        self._confirmar('20000')
        mensaje = Notificacion.objects.get(cita=self.cita, tipo='confirmacion_abono').mensaje
        self.assertIn('Pagaste: $20.000', mensaje)
        self.assertIn('Por pagar en tu cita: $30.000', mensaje)

    def test_cliente_reporta_lo_que_pago(self, *mocks):
        self.client.logout()
        session = self.client.session
        session['clientes_verificados'] = {str(self.negocio.id): self.cliente.id}
        session.save()
        with patch('apps.notificaciones.services.NotificacionService.enviar_push'):
            self.client.post(
                reverse('public:subir_comprobante', args=[self.negocio.slug, self.cita.id]),
                {'comprobante': _imagen(), 'monto_reportado': '50.000'},
            )
        self.abono.refresh_from_db()
        self.assertEqual(self.abono.monto_reportado, 50000)
        # Mis citas muestra la opción de pagar el total
        self.abono.comprobante = None
        self.abono.save()
        resp = self.client.get(reverse('public:mis_citas', args=[self.negocio.slug]))
        self.assertContains(resp, 'Valor total')
        self.assertContains(resp, '$50.000')


@patch('apps.citas.signals.enviar_confirmacion_cita', create=True)
class AvisoAbonoVencidoSoloCitasFuturasTests(TestCase):

    def setUp(self):
        admin = Usuario.objects.create_user(telefono='3000000000', password='x', nombre='A', email='a@a.com')
        self.negocio = Negocio.objects.create(administrador=admin, nombre='Spa', telefono='3000000000')
        self.servicio = Servicio.objects.create(negocio=self.negocio, nombre='M', precio=50000, duracion_minutos=60)
        self.cliente = Cliente.objects.create(negocio=self.negocio, nombre='Ana', telefono='3001111111')

    def _abono_vencido(self, dias_cita):
        cita = Cita.objects.create(
            negocio=self.negocio, cliente=self.cliente, servicio=self.servicio,
            fecha_hora=timezone.now() + timedelta(days=dias_cita), duracion_minutos=60,
            estado='pendiente_abono',
        )
        return Abono.objects.create(
            cita=cita, monto=20000, metodo_pago='transferencia', estado='pendiente',
            fecha_limite=timezone.now() - timedelta(hours=1),
        )

    @patch('apps.notificaciones.services.NotificacionService.enviar_push', return_value={'success': True})
    def test_no_avisa_abonos_de_citas_pasadas(self, enviar_push, *mocks):
        pasada = self._abono_vencido(-10)
        futura = self._abono_vencido(1)
        verificar_abonos_pendientes()

        pasada.refresh_from_db()
        futura.refresh_from_db()
        self.assertEqual(pasada.estado, 'vencido')  # el estado sí se actualiza
        self.assertEqual(futura.estado, 'vencido')
        self.assertEqual(enviar_push.call_count, 1)  # solo se avisa la futura
        self.assertEqual(enviar_push.call_args.kwargs['cita'], futura.cita)
