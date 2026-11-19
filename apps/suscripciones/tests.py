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

        negocio = Negocio.objects.get(administrador__telefono='+573005555555')
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


class RegistroAntibotsTests(TestCase):
    """Filtros contra el bot que llenaba el registro (ver antibots.py)"""

    def setUp(self):
        import time
        from django.core.cache import cache
        from .antibots import marca_formulario
        cache.clear()
        self.addCleanup(cache.clear)
        self.url = reverse('suscripciones:registro_negocio')
        self.datos = {
            'nombre': 'Ana', 'apellido': 'López', 'telefono': '300 555 5555',
            'email': 'ana@correo.com', 'marca': marca_formulario(time.time() - 10),
        }

    def _registrar(self, **cambios):
        return self.client.post(self.url, {**self.datos, **cambios}, follow=True)

    def test_persona_se_registra_y_recibe_email(self):
        from django.core import mail
        self._registrar()
        self.assertTrue(RegistroNegocio.objects.filter(telefono='+573005555555').exists())
        self.assertEqual(len(mail.outbox), 1)

    def test_formulario_muestra_marca_y_campo_trampa(self):
        resp = self.client.get(self.url)
        self.assertContains(resp, 'name="marca"')
        self.assertContains(resp, 'name="sitio_web"')
        self.assertNotContains(resp, 'cf-turnstile')

    def _assert_descartado_en_silencio(self, resp):
        from django.core import mail
        self.assertRedirects(resp, reverse('suscripciones:registro_pendiente'))
        self.assertFalse(RegistroNegocio.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_bot_que_llena_el_campo_trampa(self):
        self._assert_descartado_en_silencio(self._registrar(sitio_web='http://spam.com'))

    def test_bot_sin_marca_o_con_marca_falsa(self):
        self._assert_descartado_en_silencio(self._registrar(marca=''))
        self._assert_descartado_en_silencio(self._registrar(marca='123'))

    def test_bot_que_envia_en_menos_de_3_segundos(self):
        from .antibots import marca_formulario
        self._assert_descartado_en_silencio(self._registrar(marca=marca_formulario()))

    def test_solo_numeros_de_colombia(self):
        resp = self._registrar(telefono='+1 202 555 0143')
        self.assertContains(resp, 'solo aceptamos números de celular de Colombia')
        self.assertFalse(RegistroNegocio.objects.exists())

    def test_limite_de_3_registros_por_hora(self):
        for i in range(3):
            self._registrar(telefono=f'300 555 000{i}', email=f'ana{i}@correo.com')
        resp = self._registrar(telefono='300 555 0009', email='otra@correo.com')
        self.assertContains(resp, 'muchos intentos de registro')
        self.assertEqual(RegistroNegocio.objects.count(), 3)

    def test_turnstile_rechazado_y_aceptado(self):
        from unittest.mock import patch
        from django.test import override_settings
        with override_settings(TURNSTILE_SITE_KEY='sitio', TURNSTILE_SECRET_KEY='secreto'):
            self.assertContains(self.client.get(self.url), 'data-sitekey="sitio"')
            with patch('apps.suscripciones.antibots.requests.post') as verificar:
                verificar.return_value.json.return_value = {'success': False}
                resp = self._registrar(**{'cf-turnstile-response': 'token-malo'})
                self.assertContains(resp, 'no eres un robot')
                self.assertFalse(RegistroNegocio.objects.exists())

                verificar.return_value.json.return_value = {'success': True}
                self._registrar(**{'cf-turnstile-response': 'token-bueno'})
                self.assertTrue(RegistroNegocio.objects.exists())
