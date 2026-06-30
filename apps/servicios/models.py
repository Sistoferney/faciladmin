"""
Modelos para gestión de servicios
RF-13 a RF-15
"""
from django.db import models
from apps.negocios.models import Negocio


class Servicio(models.Model):
    """
    Modelo de servicios ofrecidos por el negocio
    RF-13: Crear servicios
    RF-14: Definir duración, precio y frecuencia
    RF-15: Activar/desactivar servicios
    """

    negocio = models.ForeignKey(
        Negocio,
        on_delete=models.CASCADE,
        related_name='servicios',
        verbose_name='Negocio'
    )

    # Información básica
    nombre = models.CharField('Nombre del servicio', max_length=200)
    descripcion = models.TextField('Descripción', blank=True)

    # RF-14: Precio y duración
    precio = models.DecimalField('Precio', max_digits=10, decimal_places=2)
    duracion_minutos = models.IntegerField(
        'Duración (minutos)',
        help_text='Duración estimada del servicio en minutos'
    )

    # RF-14: Frecuencia sugerida (clave para fidelización)
    frecuencia_dias = models.IntegerField(
        'Frecuencia sugerida (días)',
        null=True,
        blank=True,
        help_text='Cada cuántos días se recomienda repetir este servicio (ej: 30 días para corte de cabello)'
    )

    # Personalización
    imagen = models.ImageField('Imagen del servicio', upload_to='servicios/', blank=True, null=True)
    orden = models.IntegerField('Orden de visualización', default=0)

    # RF-15: Estado
    esta_activo = models.BooleanField('Activo', default=True)

    # Servicio a domicilio que requiere coordinación directa
    requiere_contacto_directo = models.BooleanField(
        'Requiere coordinación directa',
        default=False,
        help_text='Marcar si este servicio requiere contactar directamente para coordinar (ej: servicios a domicilio que dependen de distancia y disponibilidad)'
    )

    # Configuración de abono específico del servicio (opcional)
    requiere_abono = models.BooleanField(
        'Requiere abono específico',
        default=False,
        help_text='Si está marcado, sobrescribe la configuración general del negocio'
    )
    monto_abono = models.DecimalField(
        'Monto de abono',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Monto fijo de abono para este servicio'
    )
    porcentaje_abono = models.DecimalField(
        'Porcentaje de abono (%)',
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Porcentaje del precio como abono'
    )

    # Metadata
    fecha_creacion = models.DateTimeField('Fecha de creación', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField('Última actualización', auto_now=True)

    class Meta:
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'
        ordering = ['negocio', 'orden', 'nombre']
        unique_together = ('negocio', 'nombre')

    def __str__(self):
        return f"{self.nombre} - ${self.precio}"

    def clean(self):
        """
        Validaciones personalizadas
        """
        from django.core.exceptions import ValidationError

        # Validar que la duración no supere 360 minutos (6 horas)
        if self.duracion_minutos:
            if self.duracion_minutos < 5:
                raise ValidationError({'duracion_minutos': 'La duración mínima es de 5 minutos.'})
            if self.duracion_minutos > 360:
                raise ValidationError({'duracion_minutos': 'La duración máxima es de 360 minutos (6 horas).'})

    @property
    def precio_abono(self):
        """
        RF-49: Calcula el monto de abono requerido
        """
        # Si el servicio tiene abono específico
        if self.requiere_abono:
            if self.monto_abono:
                return self.monto_abono
            elif self.porcentaje_abono:
                return (self.precio * self.porcentaje_abono) / 100

        # Si no, usar configuración del negocio
        if self.negocio.requiere_abono:
            if self.negocio.monto_abono_fijo:
                return self.negocio.monto_abono_fijo
            else:
                return (self.precio * self.negocio.porcentaje_abono) / 100

        return 0

    @property
    def requiere_pago_abono(self):
        """Determina si este servicio requiere abono"""
        return self.requiere_abono or self.negocio.requiere_abono
