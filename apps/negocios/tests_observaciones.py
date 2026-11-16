"""
Observaciones de la atención: lo que se le hizo al cliente en cada cita (ej:
la referencia del tinte) para repetirlo igual en la próxima del mismo servicio.
"""
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from apps.authentication.models import Usuario
from apps.citas.models import Cita, ultimas_observaciones
from apps.clientes.models import Cliente
from apps.notificaciones.models import Pendiente
from apps.servicios.models import Servicio

from .models import Negocio
from .tests_agendar_dueno import _a_las, _base


@patch('apps.notificaciones.services.NotificacionService')
class ObservacionesTests(TestCase):

    def setUp(self):
        self.negocio, self.tinte = _base()
        self.tinte.nombre = 'Tinte'
        self.tinte.save()
        self.corte = Servicio.objects.create(negocio=self.negocio, nombre='Corte dama', precio=20000, duracion_minutos=30)
        self.cliente = Cliente.objects.create(negocio=self.negocio, nombre='Ana', telefono='3001111111')
        self.client.force_login(self.negocio.administrador)

    def _cita(self, dias, servicio=None, estado='confirmada', observaciones=''):
        return Cita.objects.create(
            negocio=self.negocio, cliente=self.cliente, servicio=servicio or self.tinte,
            fecha_hora=_a_las(dias), duracion_minutos=30, estado=estado, observaciones=observaciones,
        )

    def test_completar_guarda_observaciones_y_muestra_la_ultima_vez(self, *mocks):
        self._cita(-60, estado='completada', observaciones='Igora 6-0 + 20 vol')
        self._cita(-30, estado='completada', observaciones='Igora 7-1 + 20 vol, 35 min')
        self._cita(-10, servicio=self.corte, estado='completada', observaciones='Capas largas')
        hoy = self._cita(0)
        url = reverse('public:cita_completar', args=[self.negocio.slug, hoy.id])

        resp = self.client.get(url)
        # La más reciente del mismo servicio (no la del corte)
        self.assertContains(resp, 'Igora 7-1 + 20 vol, 35 min')
        self.assertNotContains(resp, 'Capas largas')
        self.assertContains(resp, 'Usar lo mismo')

        self.client.post(url, {'observaciones': '  Igora 7-1 + 30 vol  '})
        hoy.refresh_from_db()
        self.assertEqual(hoy.estado, 'completada')
        self.assertEqual(hoy.observaciones, 'Igora 7-1 + 30 vol')
        self.assertEqual(hoy.observaciones_por, self.negocio.administrador)
        self.assertIsNotNone(hoy.observaciones_en)

    def test_completar_sin_observaciones_sigue_igual(self, *mocks):
        cita = self._cita(0)
        resp = self.client.get(reverse('public:cita_completar', args=[self.negocio.slug, cita.id]))
        self.assertNotContains(resp, 'Usar lo mismo')
        self.client.post(reverse('public:cita_completar', args=[self.negocio.slug, cita.id]))
        cita.refresh_from_db()
        self.assertEqual(cita.estado, 'completada')
        self.assertEqual(cita.observaciones, '')
        self.assertIsNone(cita.observaciones_por)

    def test_historial_del_cliente_y_edicion(self, *mocks):
        tinte = self._cita(-30, estado='completada', observaciones='Igora 7-1')
        corte = self._cita(-10, servicio=self.corte, estado='completada')
        url = reverse('public:admin_cliente_historial', args=[self.negocio.slug, self.cliente.id])

        resp = self.client.get(url)
        self.assertContains(resp, 'Igora 7-1')
        self.assertContains(resp, 'Corte dama')
        resp = self.client.get(url, {'servicio': self.corte.id})
        self.assertNotContains(resp, 'Igora 7-1')
        self.assertContains(resp, 'Agregar observaciones')

        pendientes_antes = Pendiente.objects.count()
        resp = self.client.post(
            reverse('public:cita_observaciones', args=[self.negocio.slug, corte.id]),
            {'observaciones': 'Capas, sin flequillo'},
        )
        self.assertRedirects(resp, f'{url}#cita-{corte.id}', fetch_redirect_response=False)
        corte.refresh_from_db()
        self.assertEqual(corte.observaciones, 'Capas, sin flequillo')
        # Corregir una observación no es una novedad de la cita
        self.assertEqual(Pendiente.objects.count(), pendientes_antes)

        # Borrarla deja la cita sin autor
        self.client.post(reverse('public:cita_observaciones', args=[self.negocio.slug, tinte.id]), {'observaciones': ''})
        tinte.refresh_from_db()
        self.assertEqual(tinte.observaciones, '')
        self.assertIsNone(tinte.observaciones_por)

    def test_agenda_y_nueva_cita_muestran_la_ultima_vez(self, *mocks):
        self._cita(-30, estado='completada', observaciones='Igora 7-1')
        proxima = self._cita(2)
        resp = self.client.get(reverse('public:admin_agenda', args=[self.negocio.slug]), {'fecha': proxima.fecha_hora.date().isoformat()})
        self.assertContains(resp, '"ultima_vez": {"fecha"')
        self.assertContains(resp, 'Igora 7-1')

        datos = self.client.get(
            reverse('public:admin_cliente_buscar', args=[self.negocio.slug]), {'telefono': '3001111111'}
        ).json()
        self.assertEqual(datos['ultimas_observaciones'][str(self.tinte.id)]['texto'], 'Igora 7-1')
        self.assertNotIn(str(self.corte.id), datos['ultimas_observaciones'])

    def test_ultimas_observaciones_no_mira_citas_posteriores(self, *mocks):
        antes = self._cita(-30, estado='completada', observaciones='Antes')
        cita = self._cita(-10, estado='completada')
        self._cita(-1, estado='completada', observaciones='Después')
        self.assertEqual(ultimas_observaciones([cita]), {cita.id: antes})
        self.assertEqual(ultimas_observaciones([antes]), {})

    def test_otro_negocio_no_ve_ni_edita(self, *mocks):
        cita = self._cita(-1, estado='completada', observaciones='Privado')
        otro_admin = Usuario.objects.create_user(telefono='3009990000', password='x', nombre='Otro', email='o@o.com')
        otro = Negocio.objects.create(administrador=otro_admin, nombre='Otro Spa', telefono='3009990000')
        self.client.force_login(otro_admin)
        # Por su propio panel tampoco: el cliente y la cita son de otro negocio
        self.assertEqual(self.client.get(reverse('public:admin_cliente_historial', args=[otro.slug, self.cliente.id])).status_code, 404)
        self.assertEqual(self.client.post(reverse('public:cita_observaciones', args=[otro.slug, cita.id]), {'observaciones': 'x'}).status_code, 404)
        cita.refresh_from_db()
        self.assertEqual(cita.observaciones, 'Privado')


@patch('apps.notificaciones.services.NotificacionService')
class GuiaObservacionesTests(TestCase):
    """Etapa 2: cada servicio puede decir qué anotar y pedir que no se olvide"""

    def setUp(self):
        self.negocio, self.tinte = _base()
        self.cliente = Cliente.objects.create(negocio=self.negocio, nombre='Ana', telefono='3001111111')
        self.client.force_login(self.negocio.administrador)

    def _cita(self, dias, estado='confirmada', observaciones=''):
        return Cita.objects.create(
            negocio=self.negocio, cliente=self.cliente, servicio=self.tinte,
            fecha_hora=_a_las(dias), duracion_minutos=30, estado=estado, observaciones=observaciones,
        )

    def test_el_dueno_configura_la_guia_del_servicio(self, *mocks):
        from .forms import ServicioForm
        datos = {k: v for k, v in ServicioForm(instance=self.tinte).initial.items()
                 if v not in (None, '') and k != 'imagen'}
        datos.update(guia_observaciones='Marca, tono, oxigenada y tiempo', pedir_observaciones='on')
        resp = self.client.post(reverse('public:servicio_editar', args=[self.negocio.slug, self.tinte.id]), datos)
        self.assertEqual(resp.status_code, 302)
        self.tinte.refresh_from_db()
        self.assertEqual(self.tinte.guia_observaciones, 'Marca, tono, oxigenada y tiempo')
        self.assertTrue(self.tinte.pedir_observaciones)

    def test_completar_muestra_la_guia_y_destaca_el_campo(self, *mocks):
        cita = self._cita(0)
        url = reverse('public:cita_completar', args=[self.negocio.slug, cita.id])
        resp = self.client.get(url)
        self.assertNotContains(resp, 'Anota lo que hiciste')

        self.tinte.guia_observaciones = 'Marca, tono, oxigenada y tiempo'
        self.tinte.pedir_observaciones = True
        self.tinte.save()
        resp = self.client.get(url)
        self.assertContains(resp, 'Anota lo que hiciste')
        self.assertContains(resp, '<i class="bi bi-list-check"></i> Marca, tono, oxigenada y tiempo')
        self.assertContains(resp, 'autofocus')

        # No es obligatorio: se puede completar sin anotar
        self.client.post(url)
        cita.refresh_from_db()
        self.assertEqual(cita.estado, 'completada')

    def test_completada_sin_anotar_se_senala(self, *mocks):
        self.tinte.pedir_observaciones = True
        self.tinte.save()
        sin_anotar = self._cita(-2, estado='completada')
        self._cita(-1, estado='completada', observaciones='Igora 7-1')

        historial = self.client.get(reverse('public:admin_cliente_historial', args=[self.negocio.slug, self.cliente.id]))
        self.assertContains(historial, 'Sin anotar', count=1)

        agenda = self.client.get(reverse('public:admin_agenda', args=[self.negocio.slug]),
                                 {'fecha': sin_anotar.fecha_hora.date().isoformat()})
        self.assertContains(agenda, '"falta_anotar": true')
