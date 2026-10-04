"""
Tests de la mini página pública del negocio
"""
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.authentication.models import Usuario
from apps.citas.models import Cita
from apps.clientes.models import Cliente
from apps.servicios.models import Servicio

from .models import Negocio


@patch('apps.citas.signals.enviar_confirmacion_cita', create=True)
@patch('apps.notificaciones.services.NotificacionService')
class GestionCitasClienteTests(TestCase):
    """
    Un cliente solo puede ver, editar o cancelar sus propias citas,
    después de identificarse con su teléfono (o de agendar).
    """

    def setUp(self):
        admin = Usuario.objects.create_user(
            telefono='3000000000', password='x', nombre='Admin', email='a@a.com'
        )
        self.negocio = Negocio.objects.create(
            administrador=admin, nombre='Spa Prueba', telefono='3000000000'
        )
        servicio = Servicio.objects.create(
            negocio=self.negocio, nombre='Corte', precio=10000, duracion_minutos=30
        )
        self.cliente = Cliente.objects.create(
            negocio=self.negocio, nombre='Ana', telefono='3001111111'
        )
        otro = Cliente.objects.create(
            negocio=self.negocio, nombre='Beto', telefono='3002222222'
        )
        fecha = timezone.now() + timedelta(days=3)
        self.cita_propia = Cita.objects.create(
            negocio=self.negocio, cliente=self.cliente, servicio=servicio,
            fecha_hora=fecha, duracion_minutos=30, estado='confirmada'
        )
        self.cita_ajena = Cita.objects.create(
            negocio=self.negocio, cliente=otro, servicio=servicio,
            fecha_hora=fecha, duracion_minutos=30, estado='confirmada'
        )

    def _url(self, nombre, cita):
        return reverse(f'public:{nombre}', args=[self.negocio.slug, cita.id])

    def _identificarse(self):
        self.client.post(
            reverse('public:mis_citas', args=[self.negocio.slug]),
            {'telefono': '3001111111'},
        )

    def test_sin_identificarse_no_puede_cancelar(self, *mocks):
        resp = self.client.post(self._url('cancelar_cita_cliente', self.cita_propia))
        self.assertRedirects(resp, reverse('public:mis_citas', args=[self.negocio.slug]))
        self.cita_propia.refresh_from_db()
        self.assertEqual(self.cita_propia.estado, 'confirmada')

    def test_no_puede_cancelar_cita_ajena(self, *mocks):
        self._identificarse()
        self.client.post(self._url('cancelar_cita_cliente', self.cita_ajena))
        self.cita_ajena.refresh_from_db()
        self.assertEqual(self.cita_ajena.estado, 'confirmada')

    def test_puede_cancelar_cita_propia(self, *mocks):
        self._identificarse()
        self.client.post(self._url('cancelar_cita_cliente', self.cita_propia))
        self.cita_propia.refresh_from_db()
        self.assertEqual(self.cita_propia.estado, 'cancelada')

    def test_no_puede_ver_edicion_de_cita_ajena(self, *mocks):
        self._identificarse()
        resp = self.client.get(self._url('editar_cita_cliente', self.cita_ajena))
        self.assertEqual(resp.status_code, 302)

    def test_puede_ver_edicion_de_cita_propia(self, *mocks):
        self._identificarse()
        resp = self.client.get(self._url('editar_cita_cliente', self.cita_propia))
        self.assertEqual(resp.status_code, 200)

    def test_confirmacion_requiere_ser_el_cliente(self, *mocks):
        resp = self.client.get(self._url('confirmacion_cita', self.cita_ajena))
        self.assertEqual(resp.status_code, 302)
        self._identificarse()
        resp = self.client.get(self._url('confirmacion_cita', self.cita_propia))
        self.assertEqual(resp.status_code, 200)


class DiagnosticoPushAccesoTests(TestCase):
    """
    Los diagnósticos del servidor muestran datos de todos los negocios
    y pueden enviar pushes: solo superadmins.
    """
    URLS = [
        'public:diagnostico_push_servidor',
        'public:diagnostico_vapid_config',
        'public:test_push_admin',
    ]

    def test_anonimo_recibe_404(self):
        for nombre in self.URLS:
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 404, nombre)

    def test_admin_de_negocio_recibe_404(self):
        usuario = Usuario.objects.create_user(
            telefono='3003333333', password='x', nombre='Dueño', email='d@d.com'
        )
        self.client.force_login(usuario)
        for nombre in self.URLS:
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 404, nombre)

    def test_superadmin_puede_ver_diagnostico_servidor(self):
        su = Usuario.objects.create_superuser(
            telefono='3004444444', password='x', nombre='Root', email='r@r.com'
        )
        self.client.force_login(su)
        resp = self.client.get(reverse('public:diagnostico_push_servidor'))
        self.assertEqual(resp.status_code, 200)


@patch('apps.citas.signals.enviar_confirmacion_cita', create=True)
class BuscarClienteYAgendarTests(TestCase):
    """
    buscar-cliente no debe exponer datos personales, y un cliente existente
    puede agendar sin volver a escribir su nombre.
    """

    def setUp(self):
        admin = Usuario.objects.create_user(
            telefono='3000000000', password='x', nombre='Admin', email='a@a.com'
        )
        self.negocio = Negocio.objects.create(
            administrador=admin, nombre='Spa Prueba', telefono='3000000000'
        )
        self.servicio = Servicio.objects.create(
            negocio=self.negocio, nombre='Corte', precio=10000, duracion_minutos=30
        )
        self.cliente = Cliente.objects.create(
            negocio=self.negocio, nombre='Ana María López',
            telefono='3001111111', email='ana@correo.com'
        )
        self.url_buscar = reverse('public:buscar_cliente_api', args=[self.negocio.slug])

    def test_buscar_cliente_solo_devuelve_primer_nombre(self, *mocks):
        for formato in ['3001111111', '+57 300 111 1111', '573001111111', '(300) 111-1111']:
            data = self.client.get(self.url_buscar, {'telefono': formato}).json()
            self.assertEqual(data, {'existe': True, 'nombre': 'Ana'}, formato)

    def test_buscar_cliente_no_coincide_por_sufijo(self, *mocks):
        # Antes coincidía por los últimos 9 dígitos y devolvía a otra persona
        data = self.client.get(self.url_buscar, {'telefono': '3101111111'}).json()
        self.assertEqual(data, {'existe': False})

    def test_buscar_cliente_telefono_invalido(self, *mocks):
        data = self.client.get(self.url_buscar, {'telefono': 'abc1234567890xyz'}).json()
        self.assertEqual(data, {'existe': False})

    def _agendar(self, **extra):
        fecha = timezone.localtime() + timedelta(days=3)
        datos = {
            'telefono': '+57 300 111 1111',
            'servicio': self.servicio.id,
            'fecha': fecha.strftime('%Y-%m-%d'),
            'hora': '10:00',
            **extra,
        }
        return self.client.post(reverse('public:agendar', args=[self.negocio.slug]), datos)

    def test_cliente_existente_agenda_sin_nombre(self, *mocks):
        self._agendar(nombre='', email='')
        cita = Cita.objects.get(cliente=self.cliente)
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.nombre, 'Ana María López')
        self.assertEqual(self.cliente.email, 'ana@correo.com')
        self.assertEqual(cita.negocio, self.negocio)

    def test_cliente_nuevo_requiere_nombre(self, *mocks):
        self._agendar(telefono='3009999999', nombre='')
        self.assertFalse(Cliente.objects.filter(nombre='').exists())
        self.assertEqual(Cita.objects.count(), 0)


@patch('apps.citas.signals.enviar_confirmacion_cita', create=True)
@patch('apps.notificaciones.services.NotificacionService')
class DisponibilidadTests(TestCase):
    """
    El calendario y la validación del servidor usan las mismas reglas:
    horario de atención, bloqueos y cruces con otras citas.
    """

    def setUp(self):
        from datetime import time
        admin = Usuario.objects.create_user(
            telefono='3000000000', password='x', nombre='Admin', email='a@a.com'
        )
        self.negocio = Negocio.objects.create(
            administrador=admin, nombre='Spa Prueba', telefono='3000000000',
            horario_apertura=time(9, 0), horario_cierre=time(12, 0),
        )
        self.servicio = Servicio.objects.create(
            negocio=self.negocio, nombre='Masaje', precio=10000, duracion_minutos=60
        )
        self.cliente = Cliente.objects.create(
            negocio=self.negocio, nombre='Ana', telefono='3001111111'
        )
        self.fecha = timezone.localdate() + timedelta(days=3)

    def _dt(self, hhmm):
        from datetime import datetime
        return timezone.make_aware(datetime.strptime(f'{self.fecha} {hhmm}', '%Y-%m-%d %H:%M'))

    def _horarios(self, duracion=60, **kwargs):
        from .disponibilidad import horarios_disponibles
        return horarios_disponibles(self.negocio, self.fecha, duracion, **kwargs)

    def _cita(self, hhmm, duracion=60, **extra):
        return Cita.objects.create(
            negocio=self.negocio, servicio=self.servicio,
            cliente=extra.pop('cliente', self.cliente),
            fecha_hora=self._dt(hhmm), duracion_minutos=duracion,
            estado=extra.pop('estado', 'confirmada'), **extra
        )

    def test_dia_libre_respeta_apertura_y_cierre(self, *mocks):
        # Servicio de 60 min, abierto 9-12: el último inicio posible es 11:00
        self.assertEqual(self._horarios(), ['09:00', '09:30', '10:00', '10:30', '11:00'])

    def test_cita_larga_bloquea_todo_su_rango(self, *mocks):
        # Antes solo se miraban citas que empezaron hasta 2 h antes
        self._cita('09:00', duracion=150)  # 9:00 - 11:30
        self.assertEqual(self._horarios(duracion=30), ['11:30'])

    def test_cita_cancelada_no_ocupa(self, *mocks):
        self._cita('10:00', estado='cancelada')
        self.assertIn('10:00', self._horarios())

    def test_bloqueo_de_agenda_ocupa(self, *mocks):
        from .models import BloqueoAgenda
        BloqueoAgenda.objects.create(
            negocio=self.negocio, fecha_inicio=self._dt('10:00'),
            fecha_fin=self._dt('11:00'), motivo_interno='Reunión'
        )
        self.assertEqual(self._horarios(), ['09:00', '11:00'])

    def test_dia_cerrado_por_configuracion(self, *mocks):
        from datetime import time
        from .models import ConfiguracionHorario
        ConfiguracionHorario.objects.create(
            negocio=self.negocio, dia_semana=self.fecha.weekday(), esta_abierto=False,
            hora_apertura=time(9, 0), hora_cierre=time(12, 0),
        )
        self.assertEqual(self._horarios(), [])

    def test_horario_del_dia_tiene_prioridad(self, *mocks):
        from datetime import time
        from .models import ConfiguracionHorario
        ConfiguracionHorario.objects.create(
            negocio=self.negocio, dia_semana=self.fecha.weekday(),
            hora_apertura=time(14, 15), hora_cierre=time(16, 0),
        )
        # 14:15 se redondea al siguiente intervalo
        self.assertEqual(self._horarios(), ['14:30', '15:00'])

    def test_excluir_cita_propia_al_editar(self, *mocks):
        cita = self._cita('10:00')
        self.assertNotIn('10:00', self._horarios())
        self.assertIn('10:00', self._horarios(excluir_cita_id=cita.id))

    def _agendar(self, hora, telefono='3002222222'):
        return self.client.post(reverse('public:agendar', args=[self.negocio.slug]), {
            'nombre': 'Beto', 'telefono': telefono, 'servicio': self.servicio.id,
            'fecha': self.fecha.isoformat(), 'hora': hora,
        })

    def test_agendar_rechaza_horario_ocupado_por_otro_cliente(self, *mocks):
        self._cita('10:00')
        self._agendar('10:30')  # se cruza con 10:00-11:00
        self.assertEqual(Cita.objects.count(), 1)

    def test_agendar_rechaza_fuera_de_horario(self, *mocks):
        self._agendar('11:30')  # terminaría 12:30, después del cierre
        self._agendar('07:00')
        self.assertEqual(Cita.objects.count(), 0)

    def test_agendar_horario_libre(self, *mocks):
        self._agendar('10:00')
        self.assertEqual(Cita.objects.count(), 1)

    def test_editar_rechaza_horario_ocupado(self, *mocks):
        propia = self._cita('09:00')
        self._cita('11:00', cliente=Cliente.objects.create(
            negocio=self.negocio, nombre='Otro', telefono='3003333333'))
        session = self.client.session
        session['clientes_verificados'] = {str(self.negocio.id): self.cliente.id}
        session.save()
        url = reverse('public:editar_cita_cliente', args=[self.negocio.slug, propia.id])
        datos = {'servicio': self.servicio.id, 'fecha': self.fecha.isoformat()}

        self.client.post(url, {**datos, 'hora': '11:00'})
        propia.refresh_from_db()
        self.assertEqual(timezone.localtime(propia.fecha_hora).strftime('%H:%M'), '09:00')

        # Moverla 30 min se cruza consigo misma: debe permitirse
        self.client.post(url, {**datos, 'hora': '09:30'})
        propia.refresh_from_db()
        self.assertEqual(timezone.localtime(propia.fecha_hora).strftime('%H:%M'), '09:30')

    def test_apis_del_calendario(self, *mocks):
        self._cita('09:00', duracion=120)
        resp = self.client.get(
            reverse('public:disponibilidad_api', args=[self.negocio.slug]),
            {'fecha': self.fecha.isoformat(), 'servicio': self.servicio.id},
        )
        self.assertEqual(resp.json(), {'horarios': ['11:00']})

        resp = self.client.get(
            reverse('public:fechas_disponibles_api', args=[self.negocio.slug]),
            {'servicio': self.servicio.id, 'year': self.fecha.year, 'month': self.fecha.month},
        )
        self.assertIn(self.fecha.isoformat(), resp.json()['fechas'])

    def test_api_libera_horario_de_cita_propia_al_editar(self, *mocks):
        propia = self._cita('10:00')
        url = reverse('public:disponibilidad_api', args=[self.negocio.slug])
        params = {'fecha': self.fecha.isoformat(), 'servicio': self.servicio.id, 'cita': propia.id}

        # Sin identificarse, el parámetro se ignora (no revela nada de citas ajenas)
        self.assertNotIn('10:00', self.client.get(url, params).json()['horarios'])

        session = self.client.session
        session['clientes_verificados'] = {str(self.negocio.id): self.cliente.id}
        session.save()
        self.assertIn('10:00', self.client.get(url, params).json()['horarios'])

    def test_api_no_libera_horario_de_cita_ajena(self, *mocks):
        otro = Cliente.objects.create(negocio=self.negocio, nombre='Otro', telefono='3003333333')
        ajena = self._cita('10:00', cliente=otro)
        session = self.client.session
        session['clientes_verificados'] = {str(self.negocio.id): self.cliente.id}
        session.save()
        resp = self.client.get(
            reverse('public:disponibilidad_api', args=[self.negocio.slug]),
            {'fecha': self.fecha.isoformat(), 'servicio': self.servicio.id, 'cita': ajena.id},
        )
        self.assertNotIn('10:00', resp.json()['horarios'])

    def test_pagina_editar_carga_selector_de_horarios(self, *mocks):
        propia = self._cita('10:00')
        session = self.client.session
        session['clientes_verificados'] = {str(self.negocio.id): self.cliente.id}
        session.save()
        resp = self.client.get(reverse('public:editar_cita_cliente', args=[self.negocio.slug, propia.id]))
        self.assertContains(resp, '<select class="form-select"\n                                    id="hora"')
        self.assertContains(resp, 'data-actual="10:00"')


@patch('apps.citas.signals.enviar_confirmacion_cita', create=True)
class SesionPersistentePWATests(TestCase):
    """
    La PWA instalada no debe pedir login (dueño) ni teléfono (cliente)
    cada vez que se abre.
    """

    def setUp(self):
        self.admin = Usuario.objects.create_user(
            telefono='3000000000', password='x', nombre='Admin', email='a@a.com'
        )
        self.negocio = Negocio.objects.create(
            administrador=self.admin, nombre='Spa Prueba', telefono='3000000000'
        )
        servicio = Servicio.objects.create(
            negocio=self.negocio, nombre='Corte', precio=10000, duracion_minutos=30
        )
        self.cliente = Cliente.objects.create(negocio=self.negocio, nombre='Ana', telefono='3001111111')
        self.cita = Cita.objects.create(
            negocio=self.negocio, cliente=self.cliente, servicio=servicio,
            fecha_hora=timezone.now() + timedelta(days=3), duracion_minutos=30, estado='confirmada'
        )
        self.url_mis_citas = reverse('public:mis_citas', args=[self.negocio.slug])

    def test_sesion_dura_60_dias(self, *mocks):
        from django.conf import settings
        self.assertEqual(settings.SESSION_COOKIE_AGE, 60 * 24 * 60 * 60)
        self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)

    def test_panel_sin_sesion_va_al_login_y_vuelve(self, *mocks):
        url_panel = reverse('public:admin_dashboard', args=[self.negocio.slug])
        resp = self.client.get(url_panel)
        self.assertRedirects(resp, f'/login/?next={url_panel}', fetch_redirect_response=False)

        resp = self.client.post(f'/login/?next={url_panel}', {'username': '3000000000', 'password': 'x'})
        self.assertRedirects(resp, url_panel, fetch_redirect_response=False)

    def test_mis_citas_recuerda_al_cliente(self, *mocks):
        self.client.post(self.url_mis_citas, {'telefono': '300 111 1111'})
        # Al volver a abrir (GET) ya no pide el teléfono
        resp = self.client.get(self.url_mis_citas)
        self.assertContains(resp, 'Ana')
        self.assertContains(resp, reverse('public:editar_cita_cliente', args=[self.negocio.slug, self.cita.id]))

    def test_buscar_con_otro_telefono_olvida_al_cliente(self, *mocks):
        self.client.post(self.url_mis_citas, {'telefono': '3001111111'})
        self.client.post(self.url_mis_citas, {'accion': 'salir'})
        resp = self.client.get(self.url_mis_citas)
        self.assertNotContains(resp, reverse('public:editar_cita_cliente', args=[self.negocio.slug, self.cita.id]))
        self.assertContains(resp, 'name="telefono"')

    def test_agendar_precarga_telefono_del_cliente_recordado(self, *mocks):
        url = reverse('public:agendar', args=[self.negocio.slug])
        self.assertNotContains(self.client.get(url), '+573001111111')
        self.client.post(self.url_mis_citas, {'telefono': '3001111111'})
        self.assertContains(self.client.get(url), '+573001111111')

    def test_service_worker_sin_cache_http(self, *mocks):
        resp = self.client.get('/sw.js')
        self.assertEqual(resp['Cache-Control'], 'no-cache')
        self.assertIn('faciladmin-v5', resp.content.decode())

    def test_confirmacion_ofrece_boton_de_recordatorios(self, *mocks):
        self.client.post(self.url_mis_citas, {'telefono': '3001111111'})
        resp = self.client.get(reverse('public:confirmacion_cita', args=[self.negocio.slug, self.cita.id]))
        self.assertContains(resp, 'id="btn-activar-recordatorios"')
        self.assertNotContains(resp, 'confirm(')

    def test_banners_de_instalacion(self, *mocks):
        # Mini-página: textos con el nombre del negocio, para celular y computador
        resp = self.client.get(reverse('public:minipagina', args=[self.negocio.slug]))
        self.assertContains(resp, 'Ten a Spa Prueba a un toque')
        self.assertContains(resp, 'Agregar a mi celular')
        self.assertContains(resp, 'Agregar a mi computador')
        self.assertContains(resp, 'Agregar a pantalla de inicio')

        # Panel: usa los mismos ids que pwa-register.js sabe mostrar
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('public:admin_dashboard', args=[self.negocio.slug]))
        self.assertContains(resp, 'id="install-banner"')
        self.assertContains(resp, 'id="install-banner-ios"')
        self.assertContains(resp, 'Instalar en mi computador')
        self.assertNotContains(resp, 'install-pwa-banner')

    def test_portada_muestra_mis_citas_al_cliente_reconocido(self, *mocks):
        url = reverse('public:minipagina', args=[self.negocio.slug])
        boton = 'bi-list-check'

        # Visitante desconocido: solo "Agendar Cita"
        self.assertNotContains(self.client.get(url), boton)

        # Cliente reconocido con una cita próxima: botón con contador
        self.client.post(self.url_mis_citas, {'telefono': '3001111111'})
        resp = self.client.get(url)
        self.assertContains(resp, boton)
        self.assertContains(resp, 'title="Citas próximas">1</span>')

        # Sin citas próximas (pasadas o canceladas): botón sin contador
        self.cita.estado = 'cancelada'
        self.cita.save()
        resp = self.client.get(url)
        self.assertContains(resp, boton)
        self.assertNotContains(resp, 'title="Citas próximas"')

    def test_portada_cliente_reconocido_sin_citas(self, *mocks):
        self.cita.delete()
        session = self.client.session
        session['clientes_verificados'] = {str(self.negocio.id): self.cliente.id}
        session.save()
        resp = self.client.get(reverse('public:minipagina', args=[self.negocio.slug]))
        self.assertNotContains(resp, 'bi-list-check')

    def test_alcance_del_service_worker_coincide_con_cada_app(self, *mocks):
        # Android asigna las notificaciones (y el contador del ícono) a la app
        # instalada cuyo alcance contiene el del Service Worker
        slug = self.negocio.slug
        resp = self.client.get(reverse('public:minipagina', args=[slug]))
        self.assertContains(resp, f"window.PWA_SCOPE = '/{slug}/';")
        self.assertEqual(self.client.get(reverse('public:manifest_minipagina', args=[slug])).json()['scope'], f'/{slug}/')

        self.client.force_login(self.admin)
        resp = self.client.get(reverse('public:admin_dashboard', args=[slug]))
        self.assertContains(resp, f"window.PWA_SCOPE = '/{slug}/admin/';")
        self.assertEqual(self.client.get(reverse('public:manifest_admin', args=[slug])).json()['scope'], f'/{slug}/admin/')

    def test_panel_usa_icono_de_faciladmin_y_menu_se_cierra(self, *mocks):
        # El logo del negocio es para su mini-página; el panel usa la marca FacilAdmin
        manifest = self.client.get(reverse('public:manifest_admin', args=[self.negocio.slug])).json()
        self.assertTrue(all('faciladmin-icon-' in i['src'] for i in manifest['icons']))
        self.assertEqual({i['sizes'] for i in manifest['icons']}, {'192x192', '512x512'})

        self.client.force_login(self.admin)
        resp = self.client.get(reverse('public:admin_dashboard', args=[self.negocio.slug]))
        self.assertContains(resp, 'images/faciladmin-icon-192.png')
        self.assertContains(resp, 'images/apple-touch-icon.png')
        # Fondo para cerrar el menú al tocar fuera
        self.assertContains(resp, 'id="sidebar-fondo"')
        self.assertContains(resp, 'function cerrarSidebar()')
