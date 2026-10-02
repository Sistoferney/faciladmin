"""
Modelos para sistema de abonos
RF-49 a RF-57
"""
from django.db import models
from django.conf import settings
from apps.citas.models import Cita


class Abono(models.Model):
    """
    Modelo de abonos/pagos anticipados
    RF-49: Configurar valor de abono
    RF-50: Abono mediante transferencia
    RF-51: Información para el cliente
    RF-53: Confirmación manual del admin
    """

    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmado', 'Confirmado'),
        ('rechazado', 'Rechazado'),
        ('vencido', 'Vencido'),
        ('exonerado', 'Exonerado'),  # El dueño confirmó la cita sin cobrar el abono
    ]

    METODO_PAGO_CHOICES = [
        ('transferencia', 'Transferencia Bancaria'),
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('otro', 'Otro'),
    ]

    cita = models.OneToOneField(
        Cita,
        on_delete=models.CASCADE,
        related_name='abono',
        verbose_name='Cita'
    )

    # RF-49: Monto del abono
    monto = models.DecimalField('Monto del abono', max_digits=10, decimal_places=2)  # Exigido

    # Lo que realmente se pagó: el cliente puede abonar más o pagar el total.
    # monto_reportado lo indica el cliente al enviar el comprobante (orientativo);
    # monto_pagado lo registra el dueño al confirmar (es el que cuenta).
    monto_reportado = models.DecimalField(
        'Monto reportado por el cliente', max_digits=10, decimal_places=2, null=True, blank=True
    )
    monto_pagado = models.DecimalField(
        'Monto recibido', max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Lo que el dueño confirmó haber recibido (puede ser más que el abono exigido)'
    )

    # RF-50, RF-51: Método de pago
    metodo_pago = models.CharField(
        'Método de pago',
        max_length=20,
        choices=METODO_PAGO_CHOICES,
        default='transferencia'
    )

    # RF-54: Estado
    estado = models.CharField(
        'Estado',
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente'
    )

    # Información de la transferencia
    numero_referencia = models.CharField(
        'Número de referencia',
        max_length=100,
        blank=True,
        help_text='Número de referencia de la transferencia'
    )
    comprobante = models.ImageField(
        'Comprobante de pago',
        upload_to='abonos/comprobantes/',
        blank=True,
        null=True
    )

    # RF-55: Fechas
    fecha_limite = models.DateTimeField('Fecha límite de pago')
    fecha_pago = models.DateTimeField('Fecha de pago', null=True, blank=True)

    # RF-53: Confirmación del admin
    confirmado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='abonos_confirmados',
        verbose_name='Confirmado por'
    )
    fecha_confirmacion = models.DateTimeField('Fecha de confirmación', null=True, blank=True)
    notas_admin = models.TextField('Notas del administrador', blank=True)

    # Metadata
    fecha_creacion = models.DateTimeField('Fecha de creación', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField('Última actualización', auto_now=True)

    class Meta:
        verbose_name = 'Abono'
        verbose_name_plural = 'Abonos'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Abono ${self.monto} - {self.cita.cliente.nombre} - {self.get_estado_display()}"

    def confirmar(self, usuario):
        """
        RF-53: Confirmar abono
        RF-57: Notificar confirmación
        """
        from django.utils import timezone

        self.estado = 'confirmado'
        self.confirmado_por = usuario
        self.fecha_confirmacion = timezone.now()
        self.save()

        # Confirmar la cita asociada
        self.cita.confirmar_abono(usuario)

    @property
    def monto_recibido(self):
        """Lo efectivamente recibido: solo cuenta si el dueño confirmó el pago"""
        if self.estado != 'confirmado':
            return 0
        # Abonos confirmados antes de registrar el monto real: se asume el exigido
        return self.monto_pagado if self.monto_pagado is not None else self.monto

    @property
    def por_pagar(self):
        """El cliente aún debe pagar o enviar comprobante (incluye pago rechazado o vencido)"""
        return self.estado in ('pendiente', 'vencido', 'rechazado')

    def confirmar_pago(self, usuario, monto_pagado=None):
        """
        El dueño confirma que recibió el pago. monto_pagado es lo que realmente
        llegó (puede ser más que el abono, o el total del servicio); si no se
        indica, se usa lo que reportó el cliente o, en su defecto, el exigido.
        """
        from django.utils import timezone

        self.estado = 'confirmado'
        self.confirmado_por = usuario
        self.fecha_confirmacion = timezone.now()
        self.monto_pagado = monto_pagado or self.monto_reportado or self.monto
        self.save()

        if self.cita.estado == 'pendiente_abono':
            self.cita.estado = 'confirmada'
            self.cita.save()

    def exonerar(self, usuario, nota=''):
        """
        El dueño confirma la cita sin cobrar el abono (cliente de confianza).
        Al dejar de estar 'pendiente' se detienen los recordatorios de pago
        y la alerta de abono vencido.
        """
        from django.utils import timezone

        self.estado = 'exonerado'
        self.confirmado_por = usuario
        self.fecha_confirmacion = timezone.now()
        self.notas_admin = nota
        self.save()

        if self.cita.estado == 'pendiente_abono':
            self.cita.estado = 'confirmada'
            self.cita.save()

    def rechazar(self, usuario, motivo=''):
        """
        RF-53: Rechazar abono
        RF-57: Notificar rechazo
        """
        from django.utils import timezone

        self.estado = 'rechazado'
        self.confirmado_por = usuario
        self.fecha_confirmacion = timezone.now()
        self.notas_admin = motivo
        self.save()

        # Marcar cita como cancelada
        self.cita.cancelar(f"Abono rechazado: {motivo}")

    @property
    def esta_vencido(self):
        """RF-55: Verifica si el abono está vencido"""
        from django.utils import timezone
        return timezone.now() > self.fecha_limite and self.estado == 'pendiente'

    @property
    def dias_para_vencer(self):
        """Calcula días hasta el vencimiento"""
        from django.utils import timezone
        if self.estado != 'pendiente':
            return 0
        delta = self.fecha_limite - timezone.now()
        return max(0, delta.days)
