"""
Modelos de autenticación para administradores del sistema
RF-01, RF-02, RF-03
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UsuarioManager(BaseUserManager):
    """Manager personalizado para el modelo Usuario"""

    def create_user(self, email, password=None, **extra_fields):
        """Crea y guarda un usuario regular"""
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Crea y guarda un superusuario"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractUser):
    """
    Modelo de usuario personalizado para administradores
    RF-01: Registro de administradores
    RF-02: Login con email y contraseña
    RF-03: Recuperación de contraseña
    """
    username = None  # Removemos el username
    email = models.EmailField('Correo electrónico', unique=True)
    nombre = models.CharField('Nombre completo', max_length=255)
    telefono = models.CharField('Teléfono', max_length=20, blank=True)

    # Configuración del negocio al que pertenece (OneToOne)
    # Se definirá la relación desde el modelo Negocio

    fecha_registro = models.DateTimeField('Fecha de registro', auto_now_add=True)
    esta_activo = models.BooleanField('Activo', default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre']

    objects = UsuarioManager()

    class Meta:
        verbose_name = 'Usuario Administrador'
        verbose_name_plural = 'Usuarios Administradores'
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"{self.nombre} ({self.email})"

    @property
    def tiene_negocio(self):
        """Verifica si el usuario tiene un negocio asociado"""
        return hasattr(self, 'negocio')
