"""
Tests de identificación por teléfono: el mismo número en distintos formatos
"""
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from apps.suscripciones.models import RegistroNegocio

from .models import TokenRecuperacion, Usuario
from .telefonos import normalizar_telefono, telefono_registrado

VARIANTES = [
    '3001234567',
    '300 123 4567',
    '300-123-4567',
    '(300) 123-4567',
    '+57 300 123 4567',
    '573001234567',
    '+573001234567',
]


class NormalizarTelefonoTests(TestCase):

    def test_variantes_del_mismo_numero(self):
        for variante in VARIANTES:
            self.assertEqual(normalizar_telefono(variante), '+573001234567', variante)

    def test_numeros_invalidos(self):
        for valor in ['', None, 'abc', '123']:
            self.assertIsNone(normalizar_telefono(valor), valor)

    def test_numero_distinto_no_coincide(self):
        Usuario.objects.create_user(telefono='3001234567', password='x', nombre='A', email='a@a.com')
        self.assertFalse(telefono_registrado(Usuario.objects.all(), '3001234568'))


class LoginPorTelefonoTests(TestCase):

    def _login(self, telefono, password='clave-segura-1'):
        return self.client.post(reverse('login'), {'username': telefono, 'password': password})

    def test_login_con_cualquier_formato(self):
        Usuario.objects.create_user(
            telefono='3001234567', password='clave-segura-1', nombre='Ana', email='a@a.com'
        )
        for variante in VARIANTES:
            self.client.logout()
            resp = self._login(variante)
            self.assertEqual(resp.status_code, 302, f'No pudo entrar con {variante}')

    def test_cuenta_antigua_guardada_en_otro_formato(self):
        # Cuentas anteriores a la normalización: teléfono guardado tal cual se escribió
        usuario = Usuario(telefono='300 123 4567', nombre='Ana', email='a@a.com')
        usuario.set_password('clave-segura-1')
        usuario.save()
        self.assertEqual(self._login('3001234567').status_code, 302)

    def test_contrasena_incorrecta(self):
        Usuario.objects.create_user(
            telefono='3001234567', password='clave-segura-1', nombre='Ana', email='a@a.com'
        )
        resp = self._login('300 123 4567', password='otra')
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_create_user_guarda_normalizado(self):
        usuario = Usuario.objects.create_user(
            telefono='300 123 4567', password='x', nombre='Ana', email='a@a.com'
        )
        self.assertEqual(usuario.telefono, '+573001234567')


class RegistroSinDuplicadosTests(TestCase):

    def _registrar(self, telefono):
        with patch('apps.suscripciones.views.send_mail'):
            return self.client.post(reverse('suscripciones:registro_negocio'), {
                'nombre': 'Ana', 'apellido': 'López', 'email': 'ana@correo.com',
                'telefono': telefono,
            })

    def test_registro_guarda_telefono_normalizado(self):
        self._registrar('300 123 4567')
        self.assertEqual(RegistroNegocio.objects.get().telefono, '+573001234567')

    def test_no_permite_otra_cuenta_con_variante_de_usuario_existente(self):
        Usuario.objects.create_user(telefono='3001234567', password='x', nombre='A', email='a@a.com')
        for variante in VARIANTES:
            self._registrar(variante)
        self.assertFalse(RegistroNegocio.objects.exists())

    def test_no_permite_otra_cuenta_si_usuario_antiguo_tiene_otro_formato(self):
        usuario = Usuario(telefono='(300) 123-4567', nombre='A', email='a@a.com')
        usuario.set_password('x')
        usuario.save()
        self._registrar('+57 300 123 4567')
        self.assertFalse(RegistroNegocio.objects.exists())

    def test_no_permite_registro_pendiente_duplicado(self):
        self._registrar('3001234567')
        self._registrar('+57 300-123-4567')
        self.assertEqual(RegistroNegocio.objects.count(), 1)

    def test_rechaza_telefono_invalido(self):
        resp = self._registrar('12345')
        self.assertContains(resp, 'no es válido')
        self.assertFalse(RegistroNegocio.objects.exists())


class RecuperacionPorTelefonoTests(TestCase):

    @patch('apps.authentication.views.send_mail')
    def test_recuperacion_con_otro_formato(self, *mocks):
        usuario = Usuario(telefono='300 123 4567', nombre='Ana', email='a@a.com')
        usuario.set_password('x')
        usuario.save()
        self.client.post(reverse('solicitar_recuperacion'), {'telefono': '+573001234567'})
        self.assertTrue(TokenRecuperacion.objects.filter(usuario=usuario).exists())
