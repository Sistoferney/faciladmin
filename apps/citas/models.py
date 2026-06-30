"""
Modelos para sistema de agenda y citas
RF-16 a RF-23, RF-54, RF-55, RN-01 a RN-04
"""
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.negocios.models import Negocio
from apps.clientes.models import Cliente
from apps.servicios.models import Servicio
from datetime import timedelta


class Cita(models.Model):
    """
    Modelo de citas/reservas
    RF-16 a RF-23: Sistema de reservas
    RF-54: Estados de citas
    RN-01: Un cliente puede tener múltiples citas
    RN-02: No se pueden solapar citas
    """

    ESTADO_CHOICES = [
        ('pendiente_abono', 'Pendiente de abono'),  # RF-54
        ('confirmada', 'Confirmada'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
        ('no_asistio', 'No asistió'),
    ]

    ORIGEN_CHOICES = [
        ('web', 'Reserva Web'),  # RF-16: Cliente reserva desde mini página
        ('manual', 'Registro Manual'),  # RF-21: Admin crea manualmente
        ('walk_in', 'Sin reserva previa'),  # RF-23: Cliente llegó sin reserva
    ]

    negocio = models.ForeignKey(
        Negocio,
        on_delete=models.CASCADE,
        related_name='citas',
        verbose_name='Negocio'
    )

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='citas',
        verbose_name='Cliente'
    )

    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.PROTECT,
        related_name='citas',
        verbose_name='Servicio'
    )

    # RF-17: Fecha y hora de la cita
    fecha_hora = models.DateTimeField('Fecha y hora')

    # RN-03: Duración basada en el servicio
    duracion_minutos = models.IntegerField(
        'Duración (minutos)',
        help_text='Se copia del servicio al crear la cita'
    )

    # RF-54: Estado de la cita
    estado = models.CharField(
        'Estado',
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente_abono'
    )

    # Origen de la cita
    origen = models.CharField(
        'Origen',
        max_length=20,
        choices=ORIGEN_CHOICES,
        default='web'
    )

    # Notas
    notas_cliente = models.TextField('Notas del cliente', blank=True)
    notas_internas = models.TextField('Notas internas', blank=True)

    # RF-55: Fecha límite de pago (mínimo 2 días antes)
    fecha_limite_abono = models.DateTimeField('Fecha límite de abono', null=True, blank=True)

    # Confirmación
    confirmada_por_admin = models.BooleanField('Confirmada por admin', default=False)
    fecha_confirmacion = models.DateTimeField('Fecha de confirmación', null=True, blank=True)

    # Notificaciones enviadas
    recordatorio_enviado = models.BooleanField('Recordatorio enviado', default=False)
    confirmacion_enviada = models.BooleanField('Confirmación enviada', default=False)

    # Metadata
    fecha_creacion = models.DateTimeField('Fecha de creación', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField('Última actualización', auto_now=True)

    class Meta:
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
        ordering = ['fecha_hora']
        indexes = [
            models.Index(fields=['fecha_hora']),
            models.Index(fields=['estado']),
            models.Index(fields=['negocio', 'fecha_hora']),
            models.Index(fields=['negocio', 'estado', 'fecha_hora']),  # Para filtros del panel admin
            models.Index(fields=['cliente', '-fecha_hora']),  # Para historial del cliente
            models.Index(fields=['negocio', 'cliente', 'fecha_hora', 'estado']),  # Para validar duplicados
        ]

    def __str__(self):
        return f"{self.cliente.nombre} - {self.servicio.nombre} - {self.fecha_hora.strftime('%d/%m/%Y %H:%M')}"

    def clean(self):
        """
        Validaciones personalizadas
        RN-02: No solapar citas
        RN-04: Validar frecuencia del servicio
        """
        super().clean()

        # RN-02: Verificar que no se solapen citas
        if self.fecha_hora:
            fecha_fin = self.fecha_hora + timedelta(minutes=self.duracion_minutos or 0)

            citas_solapadas = Cita.objects.filter(
                negocio=self.negocio,
                fecha_hora__lt=fecha_fin,
                fecha_hora__gte=self.fecha_hora
            ).exclude(
                pk=self.pk
            ).exclude(
                estado__in=['cancelada', 'no_asistio']
            )

            if citas_solapadas.exists():
                raise ValidationError('Ya existe una cita en este horario.')

        # RF-55: Validar que la cita sea al menos 2 días después si requiere abono
        if self.servicio and self.servicio.requiere_pago_abono:
            dias_minimos = 2
            fecha_minima = timezone.now() + timedelta(days=dias_minimos)
            if self.fecha_hora < fecha_minima:
                raise ValidationError(
                    f'Las citas que requieren abono deben agendarse con al menos {dias_minimos} días de anticipación.'
                )

    def save(self, *args, **kwargs):
        """
        Lógica al guardar
        RF-49: Configurar fecha límite de abono
        """
        # Copiar duración del servicio si no está definida
        if not self.duracion_minutos and self.servicio:
            self.duracion_minutos = self.servicio.duracion_minutos

        # RF-51: Calcular fecha límite de abono (2 días antes de la cita)
        if self.servicio and self.servicio.requiere_pago_abono and not self.fecha_limite_abono:
            self.fecha_limite_abono = self.fecha_hora - timedelta(days=2)

        # Actualizar estado basado en confirmación de abono
        if self.confirmada_por_admin and self.estado == 'pendiente_abono':
            self.estado = 'confirmada'
            self.fecha_confirmacion = timezone.now()

        super().save(*args, **kwargs)

    @property
    def fecha_fin(self):
        """Calcula la fecha/hora de fin de la cita"""
        return self.fecha_hora + timedelta(minutes=self.duracion_minutos)

    @property
    def abono_vencido(self):
        """
        RF-55: Verifica si el abono está vencido
        """
        if not self.fecha_limite_abono:
            return False
        return timezone.now() > self.fecha_limite_abono and self.estado == 'pendiente_abono'

    @property
    def dias_hasta_cita(self):
        """Calcula días hasta la cita"""
        if self.fecha_hora < timezone.now():
            return 0
        return (self.fecha_hora - timezone.now()).days

    @property
    def requiere_abono(self):
        """Verifica si la cita requiere abono"""
        return self.servicio.requiere_pago_abono

    @property
    def monto_abono(self):
        """Obtiene el monto de abono requerido"""
        return self.servicio.precio_abono

    @classmethod
    def obtener_disponibilidad(cls, negocio, fecha, servicio):
        """
        RF-17: Obtener horarios disponibles para una fecha y servicio
        """
        # Esta lógica se implementará en las vistas
        pass

    def confirmar_abono(self, usuario):
        """
        RF-53: Confirmar o rechazar cita según abono
        """
        self.confirmada_por_admin = True
        self.estado = 'confirmada'
        self.fecha_confirmacion = timezone.now()
        self.save()

    def marcar_completada(self):
        """
        RF-22: Marcar cita como completada
        """
        self.estado = 'completada'
        self.save()

        # Actualizar estadísticas del cliente
        self.cliente.actualizar_estadisticas()

    def cancelar(self, motivo=''):
        """
        RF-22: Cancelar cita
        """
        self.estado = 'cancelada'
        if motivo:
            self.notas_internas = f"{self.notas_internas}\nCancelación: {motivo}".strip()
        self.save()
