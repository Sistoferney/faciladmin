"""
Tests de las tareas de notificaciones
"""
from datetime import datetime, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.authentication.models import Usuario
from apps.citas.models import Cita
from apps.clientes.models import Cliente
from apps.negocios.models import Negocio
from apps.servicios.models import Servicio

from .models import Notificacion
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
        cliente = Cliente.objects.create(negocio=negocio, nombre='Ana', telefono='3001111111')
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
