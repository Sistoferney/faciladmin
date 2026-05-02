"""
Modelos para sistema de notificaciones
RF-28, RF-33 a RF-34, RF-56 a RF-57
"""
from django.db import models
from apps.clientes.models import Cliente
from apps.citas.models import Cita


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

        if self.canal == 'whatsapp':
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
