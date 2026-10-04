"""
Modelos para sistema de notificaciones
RF-28, RF-33 a RF-34, RF-56 a RF-57
"""
from django.db import models
from apps.clientes.models import Cliente
from apps.citas.models import Cita
import json
from django.utils import timezone


class Notificacion(models.Model):
    """
    Modelo de notificaciones enviadas
    RF-33: Notificaciones por WhatsApp, SMS, Email
    RF-34: Tipos de notificaciones
    """

    TIPO_CHOICES = [
        ('confirmacion_cita', 'Confirmación de cita'),  # RF-18
        ('recordatorio_cita', 'Recordatorio de cita'),  # RF-28
        ('recordatorio_2h', 'Recordatorio 2 horas antes'),
        ('recordatorio_abono', 'Recordatorio de abono'),  # RF-56
        ('confirmacion_abono', 'Confirmación de abono'),  # RF-57
        ('cancelacion', 'Cancelación'),  # RF-57
        ('abono_rechazado', 'Abono rechazado'),  # RF-57
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

        # En email/SMS/WhatsApp se agrega el enlace para escribir al negocio.
        # En push no: allí va como botón de la notificación.
        mensaje = self.mensaje
        if self.cita and self.canal != 'push':
            from apps.core.whatsapp import enlace_cliente_a_negocio
            enlace = enlace_cliente_a_negocio(self.cita)
            if enlace:
                mensaje = f'{mensaje}\n\n💬 ¿Dudas? Escríbenos por WhatsApp: {enlace}'

        if self.canal == 'push':
            # Push: una frase corta (Chrome oculta como "posible spam" los textos
            # largos con emojis, teléfonos y precios). El detalle está en la app.
            from .textos_push import push_cliente
            titulo, cuerpo = push_cliente(self.tipo, self.cita, self.cliente.negocio, self.asunto)
            # El recordatorio para agendar lleva directo a agendar en la mini-página
            url = f'/{self.cliente.negocio.slug}/agendar/' if self.tipo == 'sugerencia_cita' else None
            resultado = service.enviar_push(self.cliente, titulo, cuerpo, self.cita, url=url)
        elif self.canal == 'whatsapp':
            resultado = service.enviar_whatsapp(self.cliente.telefono.as_e164, mensaje)
        elif self.canal == 'sms':
            resultado = service.enviar_sms(self.cliente.telefono.as_e164, mensaje)
        elif self.canal == 'email':
            resultado = service.enviar_email(self.cliente.email, self.asunto, mensaje)
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
        return f"Suscripción Push - {self.cliente.nombre} ({timezone.localtime(self.fecha_suscripcion).strftime('%Y-%m-%d')})"

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


class Pendiente(models.Model):
    """
    Tarea pendiente del dueño en su bandeja ("Pendientes" del panel).

    No depende de que llegue el push: aunque la notificación falle, al abrir
    el panel el dueño ve lo que tiene por hacer. Hay un pendiente abierto por
    (cita, tipo); los eventos posteriores lo actualizan en vez de duplicarlo
    (p. ej. el de abono pasa de "esperando pago" a "comprobante enviado").
    Se resuelven solos cuando se hace la acción (ver pendientes.py).
    """
    TIPO_CHOICES = [
        ('cita_nueva', 'Nueva cita'),
        ('abono', 'Abono'),
        ('cita_modificada', 'Cita modificada por el cliente'),
        ('cita_cancelada', 'Cita cancelada por el cliente'),
    ]

    negocio = models.ForeignKey(
        'negocios.Negocio', on_delete=models.CASCADE, related_name='pendientes', verbose_name='Negocio'
    )
    cita = models.ForeignKey(
        Cita, on_delete=models.CASCADE, related_name='pendientes', verbose_name='Cita'
    )
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES)
    detalle = models.CharField('Detalle', max_length=200, blank=True)
    resuelto = models.BooleanField('Resuelto', default=False, db_index=True)
    creado_en = models.DateTimeField('Creado', auto_now_add=True)
    # Se actualiza con cada evento (comprobante, vencimiento...): ordena la
    # bandeja y permite al panel detectar novedades para la notificación local
    actualizado_en = models.DateTimeField('Actualizado', auto_now=True, db_index=True)
    resuelto_en = models.DateTimeField('Resuelto en', null=True, blank=True)

    class Meta:
        verbose_name = 'Pendiente'
        verbose_name_plural = 'Pendientes'
        ordering = ['-actualizado_en']
        indexes = [models.Index(fields=['negocio', 'resuelto', '-actualizado_en'])]

    def __str__(self):
        return f'{self.get_tipo_display()} - {self.cita}'

    @property
    def titulo(self):
        if self.tipo == 'abono':
            abono = getattr(self.cita, 'abono', None)
            if abono is not None:
                if abono.estado == 'vencido':
                    return 'Abono vencido'
                if abono.estado == 'rechazado':
                    return 'Pago rechazado'
                if abono.comprobante:
                    return 'Comprobante por revisar'
            return 'Esperando abono'
        return {
            'cita_nueva': 'Nueva cita',
            'cita_modificada': 'Cita modificada por el cliente',
            'cita_cancelada': 'Cita cancelada por el cliente',
        }.get(self.tipo, self.get_tipo_display())

    @property
    def texto(self):
        from .textos_push import resumen_cita
        texto = resumen_cita(self.cita)
        if self.tipo in ('abono', 'cita_cancelada') and self.detalle:
            texto += f' · {self.detalle}'
        return texto

    @property
    def icono(self):
        if self.tipo == 'abono':
            return {'Abono vencido': 'bi-alarm', 'Pago rechazado': 'bi-x-octagon',
                    'Comprobante por revisar': 'bi-receipt'}.get(self.titulo, 'bi-wallet2')
        return {'cita_nueva': 'bi-calendar-plus', 'cita_modificada': 'bi-arrow-repeat',
                'cita_cancelada': 'bi-calendar-x'}.get(self.tipo, 'bi-bell')

    @property
    def informativo(self):
        """Se resuelve marcándolo como visto (no con una acción sobre la cita)"""
        return self.tipo in ('cita_nueva', 'cita_modificada', 'cita_cancelada')
