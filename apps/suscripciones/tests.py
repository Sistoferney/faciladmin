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


class ReenvioActivacionTests(TestCase):
    """Registro sin activar: nunca queda bloqueado el teléfono"""

    def setUp(self):
        import time
        from django.core.cache import cache
        from .antibots import marca_formulario
        cache.clear()
        self.addCleanup(cache.clear)
        self.url = reverse('suscripciones:registro_negocio')
        self.url_pendiente = reverse('suscripciones:registro_pendiente')
        self.datos = {
            'nombre': 'Ana', 'apellido': 'López', 'telefono': '300 555 5555',
            'email': 'ana@correo.com', 'marca': marca_formulario(time.time() - 10),
        }

    def _registrar(self, **cambios):
        return self.client.post(self.url, {**self.datos, **cambios}, follow=True)

    def test_email_de_activacion_html_y_72_horas(self):
        from django.core import mail
        self._registrar()
        correo = mail.outbox[0]
        registro = RegistroNegocio.objects.get()
        self.assertEqual(correo.subject, 'Activa tu cuenta de facilacces')
        self.assertIn(registro.token_validacion, correo.body)
        self.assertIn(registro.token_validacion, correo.alternatives[0][0])
        self.assertGreater(registro.fecha_token_expira, timezone.now() + timedelta(hours=71))

    def test_enlace_vencido_registrarse_de_nuevo_envia_enlace_nuevo(self):
        from django.core import mail
        self._registrar()
        registro = RegistroNegocio.objects.get()
        token_viejo = registro.token_validacion
        registro.fecha_token_expira = timezone.now() - timedelta(hours=1)
        registro.save()

        self._registrar(email='ana.correcto@correo.com')

        registro.refresh_from_db()
        self.assertEqual(RegistroNegocio.objects.count(), 1)
        self.assertNotEqual(registro.token_validacion, token_viejo)
        self.assertTrue(registro.token_valido)
        self.assertEqual(registro.email, 'ana.correcto@correo.com')
        self.assertEqual(mail.outbox[-1].to, ['ana.correcto@correo.com'])
        # El enlace viejo ya no sirve
        resp = self.client.get(reverse('suscripciones:validar_email', args=[token_viejo]))
        self.assertEqual(resp.status_code, 404)

    def test_registro_completado_no_se_reutiliza(self):
        self._registrar()
        RegistroNegocio.objects.update(estado='completado')
        resp = self._registrar()
        self.assertContains(resp, 'Intenta iniciar sesión')

    def test_reenviar_email_desde_la_pagina_pendiente(self):
        from django.core import mail
        self._registrar()
        resp = self.client.get(self.url_pendiente)
        self.assertContains(resp, 'ana@correo.com')
        self.assertContains(resp, 'Reenviar email')

        resp = self.client.post(self.url_pendiente, follow=True)
        self.assertContains(resp, 'Te reenviamos el email')
        self.assertEqual(len(mail.outbox), 2)

    def test_reenviar_con_enlace_vencido_lo_renueva(self):
        self._registrar()
        RegistroNegocio.objects.update(fecha_token_expira=timezone.now() - timedelta(hours=1))
        self.client.post(self.url_pendiente)
        self.assertTrue(RegistroNegocio.objects.get().token_valido)

    def test_reenviar_maximo_3_por_hora(self):
        from django.core import mail
        self._registrar()
        for _ in range(4):
            resp = self.client.post(self.url_pendiente, follow=True)
        self.assertContains(resp, 'varias veces')
        self.assertEqual(len(mail.outbox), 4)  # el registro + 3 reenvíos

    def test_sin_registro_en_la_sesion_no_hay_boton(self):
        resp = self.client.get(self.url_pendiente)
        self.assertNotContains(resp, 'Reenviar email')

    def test_enlace_vencido_explica_como_pedir_otro(self):
        self._registrar()
        registro = RegistroNegocio.objects.get()
        RegistroNegocio.objects.update(fecha_token_expira=timezone.now() - timedelta(hours=1))
        resp = self.client.get(reverse('suscripciones:validar_email', args=[registro.token_validacion]), follow=True)
        self.assertContains(resp, 'Regístrate de nuevo con el mismo teléfono')
