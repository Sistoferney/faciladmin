"""
Tests de la bandeja de pendientes del dueño
"""
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.abonos.models import Abono
from apps.authentication.models import Usuario
from apps.citas.models import Cita
from apps.clientes.models import Cliente
from apps.negocios.models import Negocio
from apps.servicios.models import Servicio

from .models import Pendiente


@patch('apps.notificaciones.tasks.enviar_confirmacion_cita')
@patch('apps.notificaciones.services.NotificacionService.enviar_push', return_value={'success': True})
class BandejaPendientesTests(TestCase):

    def setUp(self):
        self.admin = Usuario.objects.create_user(
            telefono='3000000000', password='x', nombre='Admin', email='a@a.com'
        )
        self.negocio = Negocio.objects.create(administrador=self.admin, nombre='Spa', telefono='3000000000')
        self.servicio = Servicio.objects.create(
            negocio=self.negocio, nombre='Masaje', precio=50000, duracion_minutos=60,
            requiere_abono=True, monto_abono=20000,
        )
        self.cliente = Cliente.objects.create(negocio=self.negocio, nombre='Ana', telefono='3001111111')

    def _cita_con_abono(self, dias=4):
        cita = Cita.objects.create(
            negocio=self.negocio, cliente=self.cliente, servicio=self.servicio,
            fecha_hora=timezone.now() + timedelta(days=dias), duracion_minutos=60,
            estado='pendiente_abono',
        )
        abono = Abono.objects.create(
            cita=cita, monto=20000, metodo_pago='transferencia', estado='pendiente',
            fecha_limite=timezone.now() + timedelta(days=2),
        )
        return cita, abono

    def _abiertos(self):
        return set(Pendiente.objects.filter(resuelto=False).values_list('tipo', flat=True))

    def _identificar_cliente(self):
        session = self.client.session
        session['clientes_verificados'] = {str(self.negocio.id): self.cliente.id}
        session.save()

    def test_cita_nueva_con_abono_crea_dos_pendientes(self, *mocks):
        self._cita_con_abono()
        self.assertEqual(self._abiertos(), {'cita_nueva', 'abono'})
        p = Pendiente.objects.get(tipo='abono')
        self.assertEqual(p.titulo, 'Esperando abono')
        self.assertIn('Ana · Masaje', p.texto)

    def test_confirmar_pago_resuelve_abono_y_cita_nueva(self, *mocks):
        cita, abono = self._cita_con_abono()
        abono.confirmar_pago(self.admin, 20000)
        self.assertEqual(self._abiertos(), set())

    def test_exonerar_resuelve(self, *mocks):
        cita, abono = self._cita_con_abono()
        abono.exonerar(self.admin)
        self.assertEqual(self._abiertos(), set())

    def test_comprobante_actualiza_el_mismo_pendiente(self, *mocks):
        import tempfile
        from django.test import override_settings
        from apps.abonos.tests import _imagen
        cita, abono = self._cita_con_abono()
        self._identificar_cliente()
        with override_settings(MEDIA_ROOT=tempfile.mkdtemp()):
            self.client.post(reverse('public:subir_comprobante', args=[self.negocio.slug, cita.id]),
                             {'comprobante': _imagen(), 'monto_reportado': '20000'})
        self.assertEqual(Pendiente.objects.filter(tipo='abono').count(), 1)
        p = Pendiente.objects.get(tipo='abono')
        self.assertEqual(p.titulo, 'Comprobante por revisar')
        self.assertIn('Comprobante enviado', p.detalle)

    def test_rechazo_del_dueno_no_es_novedad(self, *mocks):
        cita, abono = self._cita_con_abono()
        antes = Pendiente.objects.get(tipo='abono').actualizado_en
        abono.estado = 'rechazado'
        abono.save()
        p = Pendiente.objects.get(tipo='abono')
        self.assertFalse(p.resuelto)
        self.assertEqual(p.titulo, 'Pago rechazado')
        self.assertEqual(p.actualizado_en, antes)  # no dispara notificación local

    def test_cliente_cancela(self, *mocks):
        cita, _ = self._cita_con_abono()
        self._identificar_cliente()
        self.client.post(reverse('public:cancelar_cita_cliente', args=[self.negocio.slug, cita.id]),
                         {'motivo': 'Me enfermé'})
        self.assertEqual(self._abiertos(), {'cita_cancelada'})
        self.assertIn('Me enfermé', Pendiente.objects.get(tipo='cita_cancelada').texto)

    def test_cliente_modifica(self, *mocks):
        cita = Cita.objects.create(
            negocio=self.negocio, cliente=self.cliente,
            servicio=Servicio.objects.create(negocio=self.negocio, nombre='Corte', precio=10000, duracion_minutos=30),
            fecha_hora=timezone.now() + timedelta(days=4), duracion_minutos=30, estado='confirmada',
        )
        from apps.negocios.disponibilidad import horarios_disponibles
        fecha = timezone.localdate() + timedelta(days=5)
        hora = horarios_disponibles(self.negocio, fecha, 30)[0]
        self._identificar_cliente()
        self.client.post(reverse('public:editar_cita_cliente', args=[self.negocio.slug, cita.id]),
                         {'servicio': cita.servicio.id, 'fecha': fecha.isoformat(), 'hora': hora})
        self.assertIn('cita_modificada', self._abiertos())

    def test_cancelar_o_completar_desde_el_panel_cierra_todo(self, *mocks):
        cita, _ = self._cita_con_abono()
        self.client.force_login(self.admin)
        self.client.post(reverse('public:cita_cancelar', args=[self.negocio.slug, cita.id]))
        self.assertEqual(self._abiertos(), set())

    def test_marcar_revisado_solo_informativos(self, *mocks):
        self._cita_con_abono()
        self.client.force_login(self.admin)
        self.client.post(reverse('public:admin_pendientes_revisados', args=[self.negocio.slug]))
        self.assertEqual(self._abiertos(), {'abono'})  # el abono requiere confirmar el pago

        p = Pendiente.objects.get(tipo='abono')
        self.client.post(reverse('public:admin_pendiente_revisado', args=[self.negocio.slug, p.id]))
        self.assertEqual(self._abiertos(), {'abono'})

    def test_otro_negocio_no_puede_resolver(self, *mocks):
        self._cita_con_abono()
        p = Pendiente.objects.get(tipo='cita_nueva')
        otro = Usuario.objects.create_user(telefono='3009999999', password='x', nombre='O', email='o@o.com')
        Negocio.objects.create(administrador=otro, nombre='Otro', telefono='3009999999')
        self.client.force_login(otro)
        self.client.post(reverse('public:admin_pendiente_revisado', args=[self.negocio.slug, p.id]))
        p.refresh_from_db()
        self.assertFalse(p.resuelto)

    def test_pagina_y_contador_del_menu(self, *mocks):
        self._cita_con_abono()
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('public:admin_pendientes', args=[self.negocio.slug]))
        self.assertContains(resp, 'Esperando abono')
        self.assertContains(resp, 'Nueva cita')
        self.assertContains(resp, 'id="contador-pendientes" class="badge bg-danger ms-auto" >2<')

    def test_estado_para_consulta_periodica(self, *mocks):
        self.client.force_login(self.admin)
        url = reverse('public:admin_pendientes_estado', args=[self.negocio.slug])

        # Primera consulta: solo marca el punto de partida
        datos = self.client.get(url).json()
        self.assertEqual(datos['total'], 0)
        self.assertEqual(datos['novedades'], [])

        cita, _ = self._cita_con_abono()
        datos = self.client.get(url, {'desde': datos['ahora']}).json()
        self.assertEqual(datos['total'], 2)
        self.assertEqual({n['titulo'] for n in datos['novedades']}, {'Nueva cita', 'Esperando abono'})
        self.assertTrue(all(n['cita_id'] == cita.id for n in datos['novedades']))

        # Sin cambios: no hay novedades
        datos = self.client.get(url, {'desde': datos['ahora']}).json()
        self.assertEqual(datos['novedades'], [])

    def test_abono_vencido_actualiza_pendiente_solo_si_la_cita_es_futura(self, *mocks):
        from apps.abonos.tasks import verificar_abonos_pendientes
        futura, abono_f = self._cita_con_abono(dias=1)
        pasada, abono_p = self._cita_con_abono(dias=-3)
        Abono.objects.filter(pk__in=[abono_f.pk, abono_p.pk]).update(
            fecha_limite=timezone.now() - timedelta(hours=1))
        Pendiente.objects.update(resuelto=True)  # partir de cero

        verificar_abonos_pendientes()

        abiertos = Pendiente.objects.filter(resuelto=False, tipo='abono')
        self.assertEqual([p.cita_id for p in abiertos], [futura.id])
        self.assertEqual(abiertos[0].titulo, 'Abono vencido')
