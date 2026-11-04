"""
Formularios de acceso

Por defecto Django arma la etiqueta y los errores con el nombre del campo de
usuario ("Teléfono"). Se muestra "Usuario" para no anunciar qué dato se usa.
"""
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth.forms import AuthenticationForm


class _TextosDeAcceso:
    error_messages = {
        'invalid_login': 'Usuario o contraseña incorrectos.',
        'inactive': 'Esta cuenta está inactiva.',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Usuario'


class FormularioAcceso(_TextosDeAcceso, AuthenticationForm):
    """Inicio de sesión de los dueños (/login/)"""


class FormularioAccesoAdmin(_TextosDeAcceso, AdminAuthenticationForm):
    """Inicio de sesión del administrador de Django (/admin/)"""
