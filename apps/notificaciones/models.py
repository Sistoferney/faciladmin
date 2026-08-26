"""
Modelos para sistema de notificaciones
RF-28, RF-33 a RF-34, RF-56 a RF-57
"""
from django.db import models
from apps.clientes.models import Cliente
from apps.citas.models import Cita
import json


class Notificacion(models.Model):
    """
    Modelo de notificaciones enviadas
    RF-33: Notificaciones por WhatsApp, SMS, Email
    RF-34: Tipos de notificaciones
    """

    TIPO_CHOICES = [
        ('confirmacion_cita', 'Confirmación de cita'),  # RF-18
        ('recordatorio_cita', 'Recordatorio de cita'),  # RF-28
        ('recordatorio_abono', 'Recordatorio de abono'),  # RF-56
        ('confirmacion_abono', 'Confirmación de abono'),  # RF-57
        ('cancelacion', 'Cancelación'),  # RF-57
        ('promocion', 'Promoción'),  # RF-34
        ('sugerencia_cita', 'Sugerencia de próxima cita'),  # RF-30
        ('reactivacion', 'Reactivación de cliente'),  # RF-32
    ]

    CANAL_CHOICES = [
        ('push', 'Push Notification'),  # PWA Push (Gratis)
        ('whatsapp', 'WhatsApp'),
        ('sms', 'SMS'),
        ('email', 'Email'),
    ]

    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('enviada', 'Enviada'),
        ('fallida', 'Fallida'),
    ]

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='notificaciones',
        verbose_name='Cliente'
    )

    cita = models.ForeignKey(
        Cita,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notificaciones',
        verbose_name='Cita relacionada'
    )

    tipo = models.CharField('Tipo', max_length=30, choices=TIPO_CHOICES)
    canal = models.CharField('Canal', max_length=20, choices=CANAL_CHOICES)
    estado = models.CharField('Estado', max_length=20, choices=ESTADO_CHOICES, default='pendiente')

    # Contenido
    asunto = models.CharField('Asunto', max_length=200, blank=True)
    mensaje = models.TextField('Mensaje')

    # Respuesta del servicio
    id_externo = models.CharField('ID externo', max_length=200, blank=True, help_text='ID de Twilio, etc.')
    error = models.TextField('Error', blank=True)

    # Metadata
    fecha_programada = models.DateTimeField('Fecha programada', null=True, blank=True)
    fecha_envio = models.DateTimeField('Fecha de envío', null=True, blank=True)
    fecha_creacion = models.DateTimeField('Fecha de creación', auto_now_add=True)

    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['estado']),
            models.Index(fields=['tipo']),
            models.Index(fields=['fecha_programada']),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.cliente.nombre} ({self.get_canal_display()})"

    def enviar(self):
        """Envía la notificación según el canal configurado"""
        from .services import NotificacionService

        service = NotificacionService()

        if self.canal == 'push':
            resultado = service.enviar_push(self.cliente, self.asunto, self.mensaje, self.cita)
        elif self.canal == 'whatsapp':
            resultado = service.enviar_whatsapp(self.cliente.telefono.as_e164, self.mensaje)
        elif self.canal == 'sms':
            resultado = service.enviar_sms(self.cliente.telefono.as_e164, self.mensaje)
        elif self.canal == 'email':
            resultado = service.enviar_email(self.cliente.email, self.asunto, self.mensaje)
        else:
            resultado = {'success': False, 'error': 'Canal no soportado'}

        # Actualizar estado
        from django.utils import timezone
        if resultado.get('success'):
            self.estado = 'enviada'
            self.fecha_envio = timezone.now()
            self.id_externo = resultado.get('id', '')
        else:
            self.estado = 'fallida'
            self.error = resultado.get('error', 'Error desconocido')

        self.save()
        return resultado


class ClientePushSubscription(models.Model):
    """
    Modelo para asociar suscripciones push con clientes
    Permite enviar notificaciones push específicas a cada cliente
    """
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='push_subscriptions',
        verbose_name='Cliente'
    )

    # Información de la suscripción push (formato Web Push API)
    endpoint = models.TextField('Endpoint', unique=True)
    auth = models.CharField('Auth', max_length=255)
    p256dh = models.CharField('P256dh', max_length=255)

    # Metadata adicional
    user_agent = models.TextField('User Agent', blank=True)
    fecha_suscripcion = models.DateTimeField('Fecha de suscripción', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField('Última actualización', auto_now=True)
    activa = models.BooleanField('Activa', default=True)

    class Meta:
        verbose_name = 'Suscripción Push de Cliente'
        verbose_name_plural = 'Suscripciones Push de Clientes'
        ordering = ['-fecha_suscripcion']
        indexes = [
            models.Index(fields=['cliente', 'activa']),
            models.Index(fields=['endpoint']),
        ]

    def __str__(self):
        return f"Suscripción Push - {self.cliente.nombre} ({self.fecha_suscripcion.strftime('%Y-%m-%d')})"

    @classmethod
    def crear_desde_subscription_info(cls, cliente, subscription_data, user_agent=''):
        """
        Crea o actualiza una suscripción push para un cliente

        Args:
            cliente: Instancia del modelo Cliente
            subscription_data: Dict con los datos de suscripción (endpoint, keys)
            user_agent: String con el user agent del navegador

        Returns:
            Instancia de ClientePushSubscription
        """
        endpoint = subscription_data.get('endpoint')
        keys = subscription_data.get('keys', {})

        if not endpoint or not keys.get('auth') or not keys.get('p256dh'):
            raise ValueError("Datos de suscripción incompletos")

        # Buscar si ya existe una suscripción con este endpoint
        subscription, created = cls.objects.update_or_create(
            endpoint=endpoint,
            defaults={
                'cliente': cliente,
                'auth': keys.get('auth'),
                'p256dh': keys.get('p256dh'),
                'user_agent': user_agent,
                'activa': True
            }
        )

        return subscription

    def to_subscription_info(self):
        """
        Convierte los datos a formato compatible con django-webpush

        Returns:
            Dict con formato de subscription_info
        """
        return {
            'endpoint': self.endpoint,
            'keys': {
                'auth': self.auth,
                'p256dh': self.p256dh
            }
        }

    def desactivar(self):
        """Marca la suscripción como inactiva en lugar de eliminarla"""
        self.activa = False
        self.save()


class UsuarioPushSubscription(models.Model):
    """
    Modelo para asociar suscripciones push con usuarios dueños de negocio
    Permite enviar notificaciones a los administradores sobre nuevas citas, etc.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='push_subscriptions',
        verbose_name='Usuario'
    )

    negocio = models.ForeignKey(
        'negocios.Negocio',
        on_delete=models.CASCADE,
        related_name='admin_push_subscriptions',
        verbose_name='Negocio',
        help_text='Negocio al que pertenece este usuario'
    )

    # Información de la suscripción push (formato Web Push API)
    endpoint = models.TextField('Endpoint', unique=True)
    auth = models.CharField('Auth', max_length=255)
    p256dh = models.CharField('P256dh', max_length=255)

    # Metadata adicional
    user_agent = models.TextField('User Agent', blank=True)
    fecha_suscripcion = models.DateTimeField('Fecha de suscripción', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField('Última actualización', auto_now=True)
    activa = models.BooleanField('Activa', default=True)

    class Meta:
        verbose_name = 'Suscripción Push de Usuario Admin'
        verbose_name_plural = 'Suscripciones Push de Usuarios Admin'
        ordering = ['-fecha_suscripcion']
        unique_together = ('user', 'endpoint')  # Un usuario puede tener el mismo endpoint en varios dispositivos
        indexes = [
            models.Index(fields=['user', 'activa']),
            models.Index(fields=['negocio', 'activa']),
            models.Index(fields=['endpoint']),
        ]

    def __str__(self):
        return f"Suscripción Push - {self.user.username} ({self.negocio.nombre})"

    @classmethod
    def crear_desde_subscription_info(cls, user, negocio, subscription_data, user_agent=''):
        """
        Crea o actualiza una suscripción push para un usuario administrador

        Args:
            user: Instancia del modelo User (dueño del negocio)
            negocio: Instancia del modelo Negocio
            subscription_data: Dict con los datos de suscripción (endpoint, keys)
            user_agent: String con el user agent del navegador

        Returns:
            Instancia de UsuarioPushSubscription
        """
        endpoint = subscription_data.get('endpoint')
        keys = subscription_data.get('keys', {})

        if not endpoint or not keys.get('auth') or not keys.get('p256dh'):
            raise ValueError("Datos de suscripción incompletos")

        # Buscar si ya existe una suscripción con este endpoint
        subscription, created = cls.objects.update_or_create(
            endpoint=endpoint,
            defaults={
                'user': user,
                'negocio': negocio,
                'auth': keys.get('auth'),
                'p256dh': keys.get('p256dh'),
                'user_agent': user_agent,
                'activa': True
            }
        )

        return subscription

    def to_subscription_info(self):
        """
        Convierte los datos a formato compatible con pywebpush

        Returns:
            Dict con formato de subscription_info
        """
        return {
            'endpoint': self.endpoint,
            'keys': {
                'auth': self.auth,
                'p256dh': self.p256dh
            }
        }

    def desactivar(self):
        """Marca la suscripción como inactiva en lugar de eliminarla"""
        self.activa = False
        self.save()
