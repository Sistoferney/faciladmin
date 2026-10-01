"""
Tests del registro y activación de cuentas
"""
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.authentication.models import Usuario
from apps.negocios.models import Negocio

from .models import RegistroNegocio, Suscripcion


class ActivarCuentaTests(TestCase):

    def setUp(self):
        self.registro = RegistroNegocio.objects.create(
            nombre='Ana', apellido='López', telefono='3005555555',
            email='ana@correo.com', token_validacion='token-prueba',
            fecha_token_expira=timezone.now() + timedelta(days=1),
        )
        self.url = reverse('suscripciones:validar_email', args=['token-prueba'])
        self.datos = {
            'nombre_negocio': 'Spa Ana',
            'password': 'clave-segura-123',
            'password_confirm': 'clave-segura-123',
        }

    def test_activacion_crea_cuenta_y_redirige_al_panel(self):
        resp = self.client.post(self.url, self.datos)

        negocio = Negocio.objects.get(administrador__telefono='3005555555')
        self.assertRedirects(resp, reverse('core:dashboard_redirect'), target_status_code=302)
        self.assertTrue(Suscripcion.objects.filter(negocio=negocio, estado='trial').exists())
        self.registro.refresh_from_db()
        self.assertEqual(self.registro.estado, 'completado')

    def test_activacion_ya_completada_redirige_al_login(self):
        self.registro.estado = 'completado'
        self.registro.save()
        resp = self.client.get(self.url)
        self.assertRedirects(resp, reverse('login'))

    def test_fallo_a_mitad_no_deja_usuario_huerfano(self):
        from unittest.mock import patch
        with patch.object(Suscripcion.objects, 'create', side_effect=RuntimeError('fallo')):
            self.client.post(self.url, self.datos)

        self.assertFalse(Usuario.objects.filter(telefono='3005555555').exists())
        self.registro.refresh_from_db()
        self.assertNotEqual(self.registro.estado, 'completado')
