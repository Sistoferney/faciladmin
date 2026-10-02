"""
Backend de autenticación por teléfono, tolerante al formato
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from .telefonos import filtrar_por_telefono


class TelefonoBackend(ModelBackend):
    """
    Permite iniciar sesión escribiendo el teléfono en cualquier formato
    (3001234567, 300 123 4567, +57 300 123 4567...), incluidas cuentas
    antiguas cuyo teléfono se guardó en otro formato.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(get_user_model().USERNAME_FIELD)
        if not username or password is None:
            return None

        for usuario in filtrar_por_telefono(get_user_model().objects.all(), username):
            if usuario.check_password(password) and self.user_can_authenticate(usuario):
                return usuario

        # Igual que ModelBackend: ejecutar el hasher aunque no exista el usuario
        # para no revelar por el tiempo de respuesta si el teléfono está registrado
        get_user_model()().set_password(password)
        return None
