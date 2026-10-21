"""
Negocios con varios especialistas: cada uno tiene su agenda y el cliente
elige con quién (o "me da igual"). Con 0 o 1 especialista todo sigue igual.
"""
from datetime import datetime, time, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.authentication.models import Usuario
from apps.citas.models import Cita
from apps.clientes.models import Cliente
from apps.servicios.models import Servicio

from . import disponibilidad as d
from .models import BloqueoAgenda, Especialista, HorarioEspecialista, Negocio


def _a_las(fecha, hora, minuto=0):
    return timezone.make_aware(datetime.combine(fecha, time(hora, minuto)))


@patch('apps.notificaciones.services.NotificacionService')
class EspecialistasTests(TestCase):

    def setUp(self):
        # La reserva tiene límite de 10 por hora por IP: que no lo agoten otras pruebas
        from django.core.cache import cache
        cache.clear()
        admin = Usuario.objects.create_user(telefono='3000000000', password='x', nombre='Admin', email='a@a.com')
        self.negocio = Negocio.objects.create(
            administrador=admin, nombre='Spa', telefono='3000000000',
            horario_apertura=time(9, 0), horario_cierre=time(12, 0),
        )
        self.unas = Servicio.objects.create(negocio=self.negocio, nombre='Uñas', precio=20000, duracion_minutos=60)
        self.corte = Servicio.objects.create(negocio=self.negocio, nombre='Corte', precio=15000, duracion_minutos=30)
        self.cliente = Cliente.objects.create(negocio=self.negocio, nombre='Ana', telefono='3001111111')
        self.manana = timezone.localdate() + timedelta(days=3)

    def _especialista(self, nombre, *servicios, **extra):
        e = Especialista.objects.create(negocio=self.negocio, nombre=nombre, **extra)
        e.servicios.set(servicios)
        return e

    def _cita(self, hora, especialista=None, servicio=None):
        servicio = servicio or self.unas
        return Cita.objects.create(
            negocio=self.negocio, cliente=self.cliente, servicio=servicio,
            fecha_hora=_a_las(self.manana, hora), duracion_minutos=servicio.duracion_minutos,
            estado='confirmada', especialista=especialista,
        )

    def _horas(self, especialista=None, servicio=None):
        servicio = servicio or self.unas
        return d.horarios_disponibles(self.negocio, self.manana, servicio.duracion_minutos,
                                      especialista=especialista, servicio=servicio)

    # ---- Una sola agenda: igual que antes ----
    def test_con_un_especialista_funciona_como_antes(self, *mocks):
        unico = self._especialista('Laura')
        self._cita(9)
        self.assertEqual(self._horas(), ['10:00', '10:30', '11:00'])
        disponible, asignado = d.resolver_especialista(self.negocio, _a_las(self.manana, 10), self.unas)
        self.assertTrue(disponible)
        self.assertEqual(asignado, unico)  # queda a su nombre

    # ---- Varios especialistas ----
    def test_cada_especialista_tiene_su_agenda(self, *mocks):
        laura = self._especialista('Laura')
        sofia = self._especialista('Sofía')
        self._cita(9, laura)
        self.assertNotIn('09:00', self._horas(laura))
        self.assertIn('09:00', self._horas(sofia))
        # "Me da igual": a las 9 todavía hay alguien libre
        self.assertIn('09:00', self._horas())
        self.assertEqual(d.especialistas_libres(self.negocio, _a_las(self.manana, 9), 60, self.unas), [sofia])

    def test_solo_quienes_hacen_el_servicio(self, *mocks):
        manicurista = self._especialista('Laura', self.unas)
        barbero = self._especialista('Pedro', self.corte)
        self.assertEqual(d.especialistas_para(self.negocio, self.unas), [manicurista])
        self._cita(9, manicurista)
        # Pedro está libre pero no hace uñas
        self.assertNotIn('09:00', self._horas())
        disponible, _ = d.resolver_especialista(self.negocio, _a_las(self.manana, 10), self.unas, barbero.id)
        self.assertFalse(disponible)

    def test_horario_propio_y_bloqueo_personal(self, *mocks):
        laura = self._especialista('Laura')
        sofia = self._especialista('Sofía', usa_horario_negocio=False)
        HorarioEspecialista.objects.create(especialista=sofia, dia_semana=self.manana.weekday(),
                                           hora_apertura=time(10, 0), hora_cierre=time(12, 0))
        self.assertEqual(self._horas(sofia), ['10:00', '10:30', '11:00'])
        BloqueoAgenda.objects.create(negocio=self.negocio, especialista=laura, motivo_interno='Cita médica',
                                     fecha_inicio=_a_las(self.manana, 9), fecha_fin=_a_las(self.manana, 12))
        self.assertEqual(self._horas(laura), [])
        self.assertEqual(self._horas(), ['10:00', '10:30', '11:00'])  # solo Sofía

    def test_bloqueo_del_negocio_aplica_a_todos(self, *mocks):
        self._especialista('Laura')
        self._especialista('Sofía')
        BloqueoAgenda.objects.create(negocio=self.negocio, motivo_interno='Fumigación',
                                     fecha_inicio=_a_las(self.manana, 9), fecha_fin=_a_las(self.manana, 12))
        self.assertEqual(self._horas(), [])

    def test_citas_sin_especialista_ocupan_a_todos(self, *mocks):
        self._especialista('Laura')
        self._especialista('Sofía')
        self._cita(9)  # cita de antes de tener especialistas
        self.assertNotIn('09:00', self._horas())

    def test_me_da_igual_reparte_el_trabajo(self, *mocks):
        laura = self._especialista('Laura', orden=1)
        sofia = self._especialista('Sofía', orden=2)
        self._cita(11, laura, self.corte)
        _, asignado = d.resolver_especialista(self.negocio, _a_las(self.manana, 9), self.unas, 'cualquiera')
        self.assertEqual(asignado, sofia)  # Laura ya tiene una cita ese día

    # ---- Reserva del cliente ----
    def _reservar(self, hora, especialista=''):
        return self.client.post(reverse('public:agendar', args=[self.negocio.slug]), {
            'telefono': '3001111111', 'servicio': self.unas.id,
            'fecha': self.manana.isoformat(), 'hora': hora, 'especialista': especialista,
        })

    def test_reserva_con_el_especialista_elegido(self, *mocks):
        self._especialista('Laura')
        sofia = self._especialista('Sofía')
        self._reservar('09:00', sofia.id)
        self.assertEqual(Cita.objects.get().especialista, sofia)

    def test_reserva_me_da_igual_asigna_a_alguien_libre(self, *mocks):
        laura = self._especialista('Laura')
        sofia = self._especialista('Sofía')
        self._cita(9, laura)
        self._reservar('09:00', 'cualquiera')
        self.assertEqual(Cita.objects.exclude(especialista=laura).get().especialista, sofia)

    def test_no_reserva_si_el_elegido_esta_ocupado(self, *mocks):
        laura = self._especialista('Laura')
        self._especialista('Sofía')
        self._cita(9, laura)
        self._reservar('09:00', laura.id)
        self.assertEqual(Cita.objects.count(), 1)

    def test_api_quien_esta_libre(self, *mocks):
        laura = self._especialista('Laura')
        self._especialista('Sofía')
        self._cita(9, laura)
        url = reverse('public:especialistas_disponibles_api', args=[self.negocio.slug])
        datos = self.client.get(url, {'servicio': self.unas.id, 'fecha': self.manana.isoformat(), 'hora': '09:00'}).json()
        self.assertEqual([e['nombre'] for e in datos['especialistas']], ['Sofía'])

    def test_api_horas_por_especialista(self, *mocks):
        laura = self._especialista('Laura')
        self._especialista('Sofía')
        self._cita(9, laura)
        url = reverse('public:disponibilidad_api', args=[self.negocio.slug])
        params = {'servicio': self.unas.id, 'fecha': self.manana.isoformat()}
        self.assertNotIn('09:00', self.client.get(url, {**params, 'especialista': laura.id}).json()['horarios'])
        self.assertIn('09:00', self.client.get(url, params).json()['horarios'])

    def test_pagina_de_reserva_ofrece_elegir_solo_con_varios(self, *mocks):
        url = reverse('public:agendar', args=[self.negocio.slug])
        self._especialista('Laura')
        self.assertFalse(self.client.get(url).context['varios_especialistas'])
        self._especialista('Sofía')
        resp = self.client.get(url)
        self.assertTrue(resp.context['varios_especialistas'])
        self.assertContains(resp, '¿Con quién quieres tu cita?')


@patch('apps.notificaciones.services.NotificacionService')
class PanelEspecialistasTests(TestCase):

    def setUp(self):
        self.admin = Usuario.objects.create_user(telefono='3000000000', password='x', nombre='Admin', email='a@a.com')
        self.negocio = Negocio.objects.create(
            administrador=self.admin, nombre='Spa', telefono='3000000000',
            horario_apertura=time(9, 0), horario_cierre=time(12, 0),
        )
        self.unas = Servicio.objects.create(negocio=self.negocio, nombre='Uñas', precio=20000, duracion_minutos=60)
        self.client.force_login(self.admin)
        self.manana = timezone.localdate() + timedelta(days=3)

    def _url(self, nombre, *args):
        return reverse(f'public:{nombre}', args=[self.negocio.slug, *args])

    def _crear(self, nombre, **extra):
        datos = {'nombre': nombre, 'cargo': 'Manicurista', 'orden': 0, 'esta_activo': 'on',
                 'usa_horario_negocio': 'on', **extra}
        return self.client.post(self._url('especialista_crear'), datos)

    def test_crear_con_servicios_y_horario_propio(self, *mocks):
        datos = {f'dia_{n}_desde': '10:00' for n in range(7)}
        datos.update({f'dia_{n}_hasta': '14:00' for n in range(7)})
        datos.update({'dia_1_trabaja': '1', 'dia_2_trabaja': '1'})
        datos['servicios'] = [self.unas.id]
        datos.pop('usa_horario_negocio', None)
        resp = self.client.post(self._url('especialista_crear'), {
            'nombre': 'Laura', 'orden': 0, 'esta_activo': 'on', **datos,
        })
        self.assertRedirects(resp, self._url('admin_especialistas'))
        laura = Especialista.objects.get()
        self.assertFalse(laura.usa_horario_negocio)
        self.assertEqual(list(laura.servicios.all()), [self.unas])
        self.assertEqual(sorted(laura.horarios.filter(esta_abierto=True).values_list('dia_semana', flat=True)), [1, 2])

    def test_horario_invalido_no_se_guarda(self, *mocks):
        datos = {f'dia_{n}_desde': '14:00' for n in range(7)}
        datos.update({f'dia_{n}_hasta': '10:00' for n in range(7)})
        datos['dia_0_trabaja'] = '1'
        self.client.post(self._url('especialista_crear'), {'nombre': 'Laura', 'orden': 0, **datos})
        self.assertFalse(Especialista.objects.exists())

    def test_no_se_desactiva_con_citas_proximas(self, *mocks):
        self._crear('Laura')
        laura = Especialista.objects.get()
        cliente = Cliente.objects.create(negocio=self.negocio, nombre='Ana', telefono='3001111111')
        Cita.objects.create(negocio=self.negocio, cliente=cliente, servicio=self.unas, especialista=laura,
                            fecha_hora=_a_las(self.manana, 9), duracion_minutos=60, estado='confirmada')
        self.client.post(self._url('especialista_eliminar', laura.id))
        laura.refresh_from_db()
        self.assertTrue(laura.esta_activo)

    def test_eliminar_sin_citas(self, *mocks):
        self._crear('Laura')
        self.client.post(self._url('especialista_eliminar', Especialista.objects.get().id))
        self.assertFalse(Especialista.objects.exists())

    def _dos_especialistas(self):
        self._crear('Laura')
        self._crear('Sofía')
        return Especialista.objects.get(nombre='Laura'), Especialista.objects.get(nombre='Sofía')

    def test_agendar_desde_el_panel_con_especialista(self, *mocks):
        _, sofia = self._dos_especialistas()
        self.client.post(self._url('cita_nueva'), {
            'telefono': '3105551234', 'nombre': 'Carla', 'servicio': self.unas.id,
            'fecha': self.manana.isoformat(), 'hora': '09:00', 'especialista': sofia.id,
        })
        self.assertEqual(Cita.objects.get().especialista, sofia)

    def test_agenda_filtrada_y_cambio_de_especialista(self, *mocks):
        laura, sofia = self._dos_especialistas()
        cliente = Cliente.objects.create(negocio=self.negocio, nombre='Ana', telefono='3001111111')
        cita = Cita.objects.create(negocio=self.negocio, cliente=cliente, servicio=self.unas, especialista=laura,
                                   fecha_hora=_a_las(self.manana, 9), duracion_minutos=60, estado='confirmada')
        resp = self.client.get(self._url('admin_agenda'), {'fecha': self.manana.isoformat(), 'especialista': sofia.id})
        self.assertNotIn(cita.id, [c['id'] for celda in resp.context['calendario_grid'].values() for c in celda['citas']])
        self.assertContains(resp, 'Ver agenda de')

        self.client.post(self._url('cita_asignar_especialista', cita.id), {'especialista': sofia.id})
        cita.refresh_from_db()
        self.assertEqual(cita.especialista, sofia)

    def test_no_cambia_a_un_especialista_ocupado(self, *mocks):
        laura, sofia = self._dos_especialistas()
        cliente = Cliente.objects.create(negocio=self.negocio, nombre='Ana', telefono='3001111111')
        Cita.objects.create(negocio=self.negocio, cliente=cliente, servicio=self.unas, especialista=sofia,
                            fecha_hora=_a_las(self.manana, 9), duracion_minutos=60, estado='confirmada')
        cita = Cita.objects.create(negocio=self.negocio, cliente=cliente, servicio=self.unas, especialista=laura,
                                   fecha_hora=_a_las(self.manana, 9), duracion_minutos=60, estado='confirmada')
        self.client.post(self._url('cita_asignar_especialista', cita.id), {'especialista': sofia.id})
        cita.refresh_from_db()
        self.assertEqual(cita.especialista, laura)

    def test_bloqueo_solo_para_un_especialista(self, *mocks):
        laura, _ = self._dos_especialistas()
        self.client.post(self._url('bloqueo_crear'), {
            'especialista': laura.id, 'motivo_interno': 'Vacaciones', 'esta_activo': 'on',
            'fecha_inicio': f'{self.manana.isoformat()}T09:00', 'fecha_fin': f'{self.manana.isoformat()}T12:00',
        })
        self.assertEqual(BloqueoAgenda.objects.get().especialista, laura)
        self.assertEqual(d.horarios_disponibles(self.negocio, self.manana, 60, especialista=laura), [])
