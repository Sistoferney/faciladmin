"""
Modelos para gestión de clientes (CRM básico)
Nota: "Cliente" en este contexto se refiere a usuarios del spa (personas que agendan citas)
RF-04 a RF-06, RF-24 a RF-27, RF-40 a RF-42, RF-43 a RF-44
"""
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from apps.negocios.models import Negocio
from django.utils import timezone


class Cliente(models.Model):
    """
    Modelo de cliente (usuario del spa que agenda citas)
    RF-04: Cliente puede agendar sin cuenta formal
    RF-05: Identificación por número celular
    RF-06: Recuperación automática de perfil por celular
    RF-24: Creación automática de perfil al agendar
    RF-25: Creación manual por administrador
    RF-42: Teléfono único por negocio
    """

    TIPO_CLIENTE_CHOICES = [
        ('nuevo', 'Nuevo'),
        ('frecuente', 'Frecuente'),
        ('inactivo', 'Inactivo'),
    ]

    negocio = models.ForeignKey(
        Negocio,
        on_delete=models.CASCADE,
        related_name='clientes',
        verbose_name='Negocio'
    )

    # RF-26: Información básica
    nombre = models.CharField('Nombre completo', max_length=200)

    # RF-05, RF-42: Teléfono como identificador único (por negocio)
    telefono = PhoneNumberField('Teléfono', region='CO')

    email = models.EmailField('Email', blank=True)

    # Dirección para servicios a domicilio
    direccion = models.CharField('Dirección', max_length=300, blank=True)
    ciudad = models.CharField('Ciudad', max_length=100, blank=True)
    codigo_postal = models.CharField('Código postal', max_length=10, blank=True)
    referencia_direccion = models.TextField(
        'Referencias de dirección',
        blank=True,
        help_text='Instrucciones adicionales para llegar (torre, apartamento, color de casa, etc.)'
    )

    # RF-43: Tipo de cliente
    tipo_cliente = models.CharField(
        'Tipo de cliente',
        max_length=20,
        choices=TIPO_CLIENTE_CHOICES,
        default='nuevo'
    )

    # Información adicional
    fecha_nacimiento = models.DateField('Fecha de nacimiento', null=True, blank=True)
    notas = models.TextField('Notas', blank=True, help_text='Notas internas sobre el cliente')

    # Fidelización
    total_citas = models.IntegerField('Total de citas', default=0)
    total_gastado = models.DecimalField('Total gastado', max_digits=10, decimal_places=2, default=0)
    ultima_visita = models.DateTimeField('Última visita', null=True, blank=True)

    # RF-40: Método de creación
    creado_manualmente = models.BooleanField(
        'Creado manualmente',
        default=False,
        help_text='Si fue creado por el administrador o automáticamente por el sistema'
    )

    # Preferencias de notificación
    acepta_whatsapp = models.BooleanField('Acepta WhatsApp', default=True)
    acepta_sms = models.BooleanField('Acepta SMS', default=True)
    acepta_email = models.BooleanField('Acepta Email', default=True)
    acepta_promociones = models.BooleanField('Acepta promociones', default=True)

    # Metadata
    fecha_registro = models.DateTimeField('Fecha de registro', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField('Última actualización', auto_now=True)
    esta_activo = models.BooleanField('Activo', default=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-ultima_visita', '-fecha_registro']
        # RF-42: Un teléfono es único por negocio
        unique_together = ('negocio', 'telefono')
        indexes = [
            models.Index(fields=['telefono']),
            models.Index(fields=['tipo_cliente']),
            models.Index(fields=['ultima_visita']),
            models.Index(fields=['negocio', 'telefono']),  # Para búsquedas rápidas de clientes
            models.Index(fields=['negocio', 'tipo_cliente', '-ultima_visita']),  # Para filtros admin
        ]

    def __str__(self):
        return f"{self.nombre} - {self.telefono}"

    def actualizar_estadisticas(self):
        """
        Actualiza las estadísticas del cliente basado en sus citas
        RF-26: Historial de citas
        """
        from apps.citas.models import Cita

        citas_completadas = self.citas.filter(estado='completada')

        self.total_citas = citas_completadas.count()
        self.total_gastado = sum(cita.servicio.precio for cita in citas_completadas)

        ultima_cita = citas_completadas.order_by('-fecha_hora').first()
        if ultima_cita:
            self.ultima_visita = ultima_cita.fecha_hora

        # Actualizar tipo de cliente basado en actividad
        self.actualizar_tipo_cliente()
        self.save()

    def actualizar_tipo_cliente(self):
        """
        RF-43: Actualiza el tipo de cliente basado en su actividad
        RF-31: Identificar clientes inactivos
        """
        if not self.ultima_visita:
            self.tipo_cliente = 'nuevo'
            return

        dias_inactivo = (timezone.now() - self.ultima_visita).days

        # Cliente inactivo: más de 90 días sin citas
        if dias_inactivo > 90:
            self.tipo_cliente = 'inactivo'
        # Cliente frecuente: 3 o más citas
        elif self.total_citas >= 3:
            self.tipo_cliente = 'frecuente'
        else:
            self.tipo_cliente = 'nuevo'

    @property
    def dias_desde_ultima_visita(self):
        """Calcula días desde la última visita"""
        if not self.ultima_visita:
            return None
        return (timezone.now() - self.ultima_visita).days

    @property
    def es_cliente_inactivo(self):
        """RF-31: Verifica si es un cliente inactivo"""
        return self.tipo_cliente == 'inactivo'

    @classmethod
    def obtener_o_crear_por_telefono(cls, negocio, telefono, nombre='', **kwargs):
        """
        RF-06: Recupera automáticamente el perfil si el teléfono existe
        RF-24: Crea automáticamente si no existe
        """
        cliente, creado = cls.objects.get_or_create(
            negocio=negocio,
            telefono=telefono,
            defaults={'nombre': nombre, 'creado_manualmente': False, **kwargs}
        )
        return cliente, creado
