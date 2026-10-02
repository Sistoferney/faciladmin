"""
Modelos de autenticación para administradores del sistema
RF-01, RF-02, RF-03
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
import uuid
from datetime import timedelta


class UsuarioManager(BaseUserManager):
    """Manager personalizado para el modelo Usuario"""

    def create_user(self, telefono, password=None, **extra_fields):
        """Crea y guarda un usuario regular usando teléfono como identificador"""
        if not telefono:
            raise ValueError('El teléfono es obligatorio')

        # Guardar siempre en formato único (+573001234567)
        from .telefonos import normalizar_telefono
        telefono = normalizar_telefono(telefono) or telefono

        # Normalizar email si se proporciona
        if 'email' in extra_fields and extra_fields['email']:
            extra_fields['email'] = self.normalize_email(extra_fields['email'])

        user = self.model(telefono=telefono, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, telefono, password=None, **extra_fields):
        """Crea y guarda un superusuario"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(telefono, password, **extra_fields)


class Usuario(AbstractUser):
    """
    Modelo de usuario personalizado para administradores
    RF-01: Registro de administradores
    RF-02: Login con teléfono y contraseña
    RF-03: Recuperación de contraseña

    IMPORTANTE: El identificador único es el TELÉFONO, no el email.
    Varios usuarios pueden compartir el mismo email.
    """
    username = None  # Removemos el username
    telefono = models.CharField('Teléfono', max_length=20, unique=True, db_index=True)
    email = models.EmailField('Correo electrónico')  # Email NO único pero requerido
    nombre = models.CharField('Nombre completo', max_length=255)

    # Configuración del negocio al que pertenece (OneToOne)
    # Se definirá la relación desde el modelo Negocio

    fecha_registro = models.DateTimeField('Fecha de registro', auto_now_add=True)
    esta_activo = models.BooleanField('Activo', default=True)

    USERNAME_FIELD = 'telefono'
    REQUIRED_FIELDS = ['nombre']

    objects = UsuarioManager()

    class Meta:
        verbose_name = 'Usuario Administrador'
        verbose_name_plural = 'Usuarios Administradores'
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"{self.nombre} ({self.telefono})"

    @property
    def tiene_negocio(self):
        """Verifica si el usuario tiene un negocio asociado"""
        return hasattr(self, 'negocio')


class TokenRecuperacion(models.Model):
    """
    Modelo para tokens de recuperación de contraseña
    RF-03: Recuperación de contraseña segura
    """
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='tokens_recuperacion',
        verbose_name='Usuario'
    )
    token = models.UUIDField(
        'Token',
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )
    fecha_creacion = models.DateTimeField('Fecha de creación', auto_now_add=True)
    fecha_expiracion = models.DateTimeField('Fecha de expiración')
    usado = models.BooleanField('Usado', default=False)
    ip_solicitud = models.GenericIPAddressField('IP de solicitud', null=True, blank=True)

    class Meta:
        verbose_name = 'Token de Recuperación'
        verbose_name_plural = 'Tokens de Recuperación'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['token', 'usado']),
            models.Index(fields=['usuario', '-fecha_creacion']),
        ]

    def __str__(self):
        return f"Token para {self.usuario.email} - {'Usado' if self.usado else 'Activo'}"

    def save(self, *args, **kwargs):
        """Establece automáticamente la fecha de expiración (1 hora desde creación)"""
        if not self.pk and not self.fecha_expiracion:
            self.fecha_expiracion = timezone.now() + timedelta(hours=1)
        super().save(*args, **kwargs)

    def es_valido(self):
        """Verifica si el token es válido (no usado y no expirado)"""
        return not self.usado and timezone.now() < self.fecha_expiracion

    def marcar_como_usado(self):
        """Marca el token como usado para prevenir reutilización"""
        self.usado = True
        self.save(update_fields=['usado'])
