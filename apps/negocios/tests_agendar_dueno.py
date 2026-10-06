"""
El dueño agenda citas desde el panel (clientes que llaman) y el cliente ve
en "Mis citas" lo que cambió desde su última visita.
"""
from datetime import datetime, time, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.abonos.models import Abono
from apps.authentication.models import Usuario
from apps.citas.models import Cita
from apps.clientes.models import Cliente
from apps.notificaciones.models import Pendiente
from apps.servicios.models import Servicio

from .models import Negocio


def _base():
    admin = Usuario.objects.create_user(
        telefono='3000000000', password='x', nombre='Admin', email='a@a.com'
    )
    negocio = Negocio.objects.create(administrador=admin, nombre='Spa Prueba', telefono='3000000000')
    servicio = Servicio.objects.create(negocio=negocio, nombre='Corte', precio=10000, duracion_minutos=30)
    return negocio, servicio


def _a_las(dias, hora=10):
    fecha = timezone.localdate() + timedelta(days=dias)
    return timezone.make_aware(datetime.combine(fecha, time(hora, 0)))


class AgendarDesdePanelTests(TestCase):

    def setUp(self):
        self.negocio, self.servicio = _base()
        self.client.force_login(self.negocio.administrador)
        self.url = reverse('public:cita_nueva', args=[self.negocio.slug])

    def _agendar(self, dias=3, hora='10:00', **extra):
        datos = {
            'telefono': '310 555 1234',
            'nombre': 'Carla Ruiz',
            'servicio': self.servicio.id,
            'fecha': (timezone.localdate() + timedelta(days=dias)).isoformat(),
            'hora': hora,
            **extra,
        }
        return self.client.post(self.url, datos)

    def test_agenda_ofrece_agendar(self):
        resp = self.client.get(reverse('public:admin_agenda', args=[self.negocio.slug]))
        self.assertContains(resp, 'agendarCitaDesdeSeleccion()')
        self.assertContains(resp, self.url)

    def test_formulario_precarga_el_espacio_elegido(self):
        resp = self.client.get(self.url, {'fecha': '2030-01-07', 'hora': '15:30'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'value="2030-01-07"')
        self.assertContains(resp, '15:30')

    def test_cliente_nuevo_se_crea_con_el_celular(self):
        resp = self._agendar()
        cliente = Cliente.objects.get(negocio=self.negocio)
        cita = Cita.objects.get(cliente=cliente)
        self.assertRedirects(resp, reverse('public:cita_agendada', args=[self.negocio.slug, cita.id]))
        self.assertEqual(cliente.nombre, 'Carla Ruiz')
        self.assertEqual(cliente.telefono.as_e164, '+573105551234')
        self.assertTrue(cliente.creado_manualmente)
        self.assertEqual(cita.estado, 'confirmada')
        self.assertEqual(cita.origen, 'manual')
        self.assertEqual(timezone.localtime(cita.fecha_hora).strftime('%H:%M'), '10:00')
        # La agendó el propio dueño: no es una novedad en su bandeja
        self.assertFalse(Pendiente.objects.exists())

    def test_cliente_existente_en_otro_formato_no_se_duplica(self):
        ana = Cliente.objects.create(negocio=self.negocio, nombre='Ana', telefono='3105551234')
        self._agendar(telefono='+57 (310) 555-1234', nombre='')
        self.assertEqual(Cliente.objects.count(), 1)
        self.assertEqual(Cita.objects.get().cliente, ana)

    def test_cliente_de_baja_se_reactiva(self):
        ana = Cliente.objects.create(negocio=self.negocio, nombre='Ana', telefono='3105551234')
        ana.dar_de_baja('No quería volver')
        self._agendar(nombre='')
        ana.refresh_from_db()
        self.assertTrue(ana.esta_activo)

    def test_cliente_nuevo_requiere_nombre(self):
        resp = self._agendar(nombre='')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Cita.objects.exists())
        self.assertFalse(Cliente.objects.exists())

    def test_celular_invalido(self):
        self._agendar(telefono='123')
        self.assertFalse(Cita.objects.exists())

    def test_no_agenda_sobre_otra_cita(self):
        otro = Cliente.objects.create(negocio=self.negocio, nombre='Beto', telefono='3002222222')
        Cita.objects.create(negocio=self.negocio, cliente=otro, servicio=self.servicio,
                            fecha_hora=_a_las(3), duracion_minutos=30, estado='confirmada')
        resp = self._agendar()
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'ya no está disponible')
        self.assertEqual(Cita.objects.count(), 1)

    def test_con_anticipo_queda_pendiente_de_abono(self):
        self.servicio.requiere_abono = True
        self.servicio.monto_abono = 5000
        self.servicio.save()
        self._agendar(pedir_abono='1')
        cita = Cita.objects.get()
        self.assertEqual(cita.estado, 'pendiente_abono')
        self.assertEqual(cita.abono.monto, 5000)
        self.assertEqual(cita.abono.estado, 'pendiente')
        # El pendiente de abono se abre cuando el cliente envíe el comprobante
        self.assertFalse(Pendiente.objects.exists())

    def test_sin_marcar_anticipo_queda_confirmada(self):
        self.servicio.requiere_abono = True
        self.servicio.monto_abono = 5000
        self.servicio.save()
        self._agendar()
        self.assertEqual(Cita.objects.get().estado, 'confirmada')
        self.assertFalse(Abono.objects.exists())

    def test_sin_margen_no_pide_anticipo(self):
        self.servicio.requiere_abono = True
        self.servicio.monto_abono = 5000
        self.servicio.save()
        self._agendar(dias=1, pedir_abono='1')
        self.assertEqual(Cita.objects.get().estado, 'confirmada')
        self.assertFalse(Abono.objects.exists())

    def test_resumen_tiene_whatsapp_con_enlace_a_mis_citas(self):
        self._agendar()
        cita = Cita.objects.get()
        resp = self.client.get(reverse('public:cita_agendada', args=[self.negocio.slug, cita.id]))
        self.assertContains(resp, 'https://wa.me/573105551234?text=')
        self.assertContains(resp, 'mis-citas')

    def test_buscar_cliente_devuelve_nombre_completo(self):
        Cliente.objects.create(negocio=self.negocio, nombre='Ana María López', telefono='3105551234')
        url = reverse('public:admin_cliente_buscar', args=[self.negocio.slug])
        datos = self.client.get(url, {'telefono': '310 555 1234'}).json()
        self.assertEqual(datos['nombre'], 'Ana María López')
        self.assertFalse(self.client.get(url, {'telefono': '3109999999'}).json()['encontrado'])

    def test_otro_usuario_no_puede_agendar(self):
        intruso = Usuario.objects.create_user(telefono='3009999999', password='x', nombre='X', email='x@x.com')
        self.client.force_login(intruso)
        self._agendar()
        self.assertFalse(Cita.objects.exists())

    @patch('apps.notificaciones.services.NotificacionService.enviar_push', return_value={'success': True})
    def test_no_avisa_al_dueno_de_su_propia_cita(self, enviar_push):
        from apps.notificaciones.tasks import enviar_confirmacion_cita
        self._agendar()
        enviar_confirmacion_cita(Cita.objects.get().id)
        self.assertFalse(any(c.kwargs.get('enviar_a_admin') for c in enviar_push.call_args_list))


@patch('apps.notificaciones.services.NotificacionService')
class AvisosMisCitasTests(TestCase):

    def setUp(self):
        self.negocio, self.servicio = _base()
        self.cliente = Cliente.objects.create(negocio=self.negocio, nombre='Ana', telefono='3001111111')
        self.url = reverse('public:mis_citas', args=[self.negocio.slug])
        self.client.post(self.url, {'telefono': '3001111111'})

    def _cita(self, **extra):
        return Cita.objects.create(
            negocio=self.negocio, cliente=self.cliente, servicio=self.servicio,
            fecha_hora=_a_las(5), duracion_minutos=30, **extra
        )

    def _avisos(self):
        return [texto for _, texto in self.client.get(self.url).context['avisos']]

    def test_primera_visita_no_avisa(self, *mocks):
        self._cita(estado='pendiente_abono')
        self.assertEqual(self._avisos(), [])

    def test_avisa_confirmacion_una_sola_vez(self, *mocks):
        cita = self._cita(estado='pendiente_abono')
        self._avisos()
        cita.estado = 'confirmada'
        cita.save()
        avisos = self._avisos()
        self.assertEqual(len(avisos), 1)
        self.assertIn('fue confirmada', avisos[0])
        self.assertEqual(self._avisos(), [])

    def test_avisa_cancelacion_del_negocio(self, *mocks):
        cita = self._cita(estado='confirmada')
        self._avisos()
        cita.cancelar('Se enfermó la estilista')
        self.assertIn('fue cancelada', self._avisos()[0])

    def test_avisa_cita_agendada_por_el_negocio(self, *mocks):
        self._avisos()
        self._cita(estado='confirmada', origen='manual')
        self.assertIn('te agendó Corte', self._avisos()[0])

    def test_no_avisa_lo_que_hizo_el_propio_cliente(self, *mocks):
        cita = self._cita(estado='confirmada')
        self._avisos()
        self.client.post(reverse('public:cancelar_cita_cliente', args=[self.negocio.slug, cita.id]))
        cita.refresh_from_db()
        self.assertEqual(cita.estado, 'cancelada')
        self.assertEqual(self._avisos(), [])

    def test_no_avisa_citas_pasadas(self, *mocks):
        cita = self._cita(estado='pendiente_abono')
        self._avisos()
        Cita.objects.filter(pk=cita.pk).update(fecha_hora=timezone.now() - timedelta(days=1), estado='cancelada')
        self.assertEqual(self._avisos(), [])
