"""
Modelos para promociones y campañas
RF-35 a RF-37
"""
from django.db import models
from django.conf import settings
from apps.negocios.models import Negocio


class Promocion(models.Model):
    """
    RF-35: Crear promociones
    RF-36: Segmentar clientes
    RF-37: Enviar campañas
    """

    SEGMENTO_CHOICES = [
        ('todos', 'Todos los clientes'),
        ('nuevos', 'Clientes nuevos'),  # RF-36
        ('frecuentes', 'Clientes frecuentes'),  # RF-36
        ('inactivos', 'Clientes inactivos'),  # RF-36
        ('personalizado', 'Segmento personalizado'),
    ]

    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('programada', 'Programada'),
        ('enviada', 'Enviada'),
        ('finalizada', 'Finalizada'),
    ]

    negocio = models.ForeignKey(
        Negocio,
        on_delete=models.CASCADE,
        related_name='promociones',
        verbose_name='Negocio'
    )

    # Información básica
    nombre = models.CharField('Nombre de la promoción', max_length=200)
    descripcion = models.TextField('Descripción')
    mensaje = models.TextField(
        'Mensaje a enviar',
        help_text='Mensaje que recibirán los clientes'
    )

    # RF-36: Segmentación
    segmento = models.CharField(
        'Segmento de clientes',
        max_length=20,
        choices=SEGMENTO_CHOICES,
        default='todos'
    )

    # Configuración
    imagen = models.ImageField('Imagen', upload_to='promociones/', blank=True, null=True)
    codigo_descuento = models.CharField('Código de descuento', max_length=50, blank=True)
    porcentaje_descuento = models.DecimalField(
        'Porcentaje de descuento',
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Programación
    fecha_inicio = models.DateTimeField('Fecha de inicio', null=True, blank=True)
    fecha_fin = models.DateTimeField('Fecha de fin', null=True, blank=True)
    fecha_envio = models.DateTimeField('Fecha de envío', null=True, blank=True)

    # Estado
    estado = models.CharField('Estado', max_length=20, choices=ESTADO_CHOICES, default='borrador')

    # Estadísticas
    total_destinatarios = models.IntegerField('Total de destinatarios', default=0)
    total_enviados = models.IntegerField('Total enviados', default=0)
    total_fallidos = models.IntegerField('Total fallidos', default=0)

    # Metadata
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='promociones_creadas',
        verbose_name='Creado por'
    )
    fecha_creacion = models.DateTimeField('Fecha de creación', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField('Última actualización', auto_now=True)

    class Meta:
        verbose_name = 'Promoción'
        verbose_name_plural = 'Promociones'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.nombre} ({self.get_estado_display()})"

    def obtener_clientes_segmento(self):
        """
        RF-36: Obtiene clientes según el segmento seleccionado
        """
        from apps.clientes.models import Cliente

        queryset = Cliente.objects.filter(
            negocio=self.negocio,
            esta_activo=True,
            acepta_promociones=True
        )

        if self.segmento == 'nuevos':
            queryset = queryset.filter(tipo_cliente='nuevo')
        elif self.segmento == 'frecuentes':
            queryset = queryset.filter(tipo_cliente='frecuente')
        elif self.segmento == 'inactivos':
            queryset = queryset.filter(tipo_cliente='inactivo')
        # Si es 'todos' o 'personalizado', devuelve todos

        return queryset

    def enviar_campana(self):
        """
        RF-37: Enviar campaña a los clientes del segmento
        """
        from apps.notificaciones.models import Notificacion

        clientes = self.obtener_clientes_segmento()
        self.total_destinatarios = clientes.count()
        enviados = 0
        fallidos = 0

        for cliente in clientes:
            # Determinar canal
            if cliente.acepta_whatsapp:
                canal = 'whatsapp'
            elif cliente.acepta_sms:
                canal = 'sms'
            elif cliente.acepta_email and cliente.email:
                canal = 'email'
            else:
                fallidos += 1
                continue

            # Personalizar mensaje
            mensaje_personalizado = self.mensaje.replace('{nombre}', cliente.nombre)
            mensaje_personalizado = mensaje_personalizado.replace('{negocio}', self.negocio.nombre)

            # Crear notificación
            notificacion = Notificacion.objects.create(
                cliente=cliente,
                tipo='promocion',
                canal=canal,
                asunto=self.nombre,
                mensaje=mensaje_personalizado
            )

            resultado = notificacion.enviar()
            if resultado.get('success'):
                enviados += 1
            else:
                fallidos += 1

        # Actualizar estadísticas
        self.total_enviados = enviados
        self.total_fallidos = fallidos
        self.estado = 'enviada'

        from django.utils import timezone
        self.fecha_envio = timezone.now()
        self.save()

        return {
            'total': self.total_destinatarios,
            'enviados': enviados,
            'fallidos': fallidos
        }
