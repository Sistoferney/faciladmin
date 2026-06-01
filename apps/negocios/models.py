"""
Modelos para gestión de negocios y mini páginas
RF-08 a RF-12
"""
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.exceptions import ValidationError
import uuid

# Palabras reservadas del sistema que no se pueden usar como slugs
SLUGS_RESERVADOS = [
    'admin', 'login', 'logout', 'registro', 'dashboard',
    'api', 'static', 'media', 'accounts',
    'auth', 'authentication', 'usuarios', 'users',
    'sistema', 'system', 'configuracion', 'config', 'settings',
    'superadmin', 'root', 'administrador',
    'precios', 'pricing', 'contacto', 'contact',
    'como-funciona', 'about', 'ayuda', 'help',
    'terminos', 'terms', 'privacidad', 'privacy',
    'legal', 'soporte', 'support',
]


class Negocio(models.Model):
    """
    Modelo del negocio (Spa, Peluquería, Barbería)
    RF-08: Crear y editar mini página
    RF-09: Enlace único compartible
    RF-10: Mostrar información del negocio
    """

    TIPO_NEGOCIO_CHOICES = [
        ('spa', 'Spa'),
        ('peluqueria', 'Peluquería'),
        ('barberia', 'Barbería'),
        ('salon_belleza', 'Salón de Belleza'),
        ('otro', 'Otro'),
    ]

    # Relación con el administrador
    administrador = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='negocio',
        verbose_name='Administrador'
    )

    # Información básica
    nombre = models.CharField('Nombre del negocio', max_length=200)
    tipo = models.CharField('Tipo de negocio', max_length=20, choices=TIPO_NEGOCIO_CHOICES, default='spa')
    descripcion = models.TextField('Descripción', blank=True)

    # URL única para mini página (RF-09)
    slug = models.SlugField('URL única', unique=True, max_length=100, blank=True)

    # Información de contacto
    telefono = models.CharField('Teléfono de contacto', max_length=20)
    email = models.EmailField('Email de contacto', blank=True)
    whatsapp = models.CharField('WhatsApp', max_length=20, blank=True)

    # Dirección
    direccion = models.CharField('Dirección', max_length=300, blank=True)
    ciudad = models.CharField('Ciudad', max_length=100, blank=True)
    estado = models.CharField('Estado', max_length=100, blank=True)
    codigo_postal = models.CharField('Código postal', max_length=10, blank=True)

    # Horarios de atención
    horario_apertura = models.TimeField('Hora de apertura', null=True, blank=True)
    horario_cierre = models.TimeField('Hora de cierre', null=True, blank=True)
    dias_atencion = models.CharField(
        'Días de atención',
        max_length=200,
        default='Lunes a Viernes',
        help_text='Ejemplo: Lunes a Viernes, Lunes a Sábado'
    )

    # Configuración de abonos
    requiere_abono = models.BooleanField('Requiere abono', default=False)
    porcentaje_abono = models.DecimalField(
        'Porcentaje de abono (%)',
        max_digits=5,
        decimal_places=2,
        default=50.00,
        help_text='Porcentaje del servicio que se requiere como abono'
    )
    monto_abono_fijo = models.DecimalField(
        'Monto fijo de abono',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Si se define, se usa este monto en lugar del porcentaje'
    )

    # Información bancaria para abonos (RF-51)
    banco = models.CharField('Banco', max_length=100, blank=True)
    numero_cuenta = models.CharField('Número de cuenta', max_length=50, blank=True)
    clabe = models.CharField('Número de cuenta bancaria', max_length=50, blank=True)
    titular_cuenta = models.CharField('Titular de la cuenta', max_length=200, blank=True)

    # Personalización de mini página
    logo = models.ImageField('Logo', upload_to='negocios/logos/', blank=True, null=True)
    imagen_portada = models.ImageField('Imagen de portada', upload_to='negocios/portadas/', blank=True, null=True)
    color_primario = models.CharField('Color primario', max_length=7, default='#007bff')
    color_secundario = models.CharField('Color secundario', max_length=7, default='#6c757d')

    # Configuración
    esta_activo = models.BooleanField('Activo', default=True)
    acepta_reservas_online = models.BooleanField('Acepta reservas online', default=True)

    # Redes sociales
    facebook = models.URLField('Facebook', blank=True)
    instagram = models.URLField('Instagram', blank=True)
    twitter = models.URLField('Twitter', blank=True)

    # Metadata
    fecha_creacion = models.DateTimeField('Fecha de creación', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField('Última actualización', auto_now=True)

    class Meta:
        verbose_name = 'Negocio'
        verbose_name_plural = 'Negocios'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.nombre

    def clean(self):
        """Validar que el slug no sea una palabra reservada"""
        super().clean()
        if self.slug and self.slug.lower() in SLUGS_RESERVADOS:
            raise ValidationError({
                'slug': f'El nombre "{self.slug}" está reservado por el sistema. Por favor elige otro nombre para tu negocio.'
            })

    def save(self, *args, **kwargs):
        """Generar slug automáticamente si no existe y validar palabras reservadas"""
        if not self.slug:
            base_slug = slugify(self.nombre)

            # Verificar si el slug base es una palabra reservada
            if base_slug.lower() in SLUGS_RESERVADOS:
                # Agregar sufijo automático para evitar palabras reservadas
                base_slug = f"{base_slug}-negocio"

            slug = base_slug
            counter = 1

            # Buscar un slug único que no esté reservado
            while Negocio.objects.filter(slug=slug).exists() or slug.lower() in SLUGS_RESERVADOS:
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        # Validación final antes de guardar
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def url_publica(self):
        """RF-09: URL única compartible"""
        return f"{settings.SITE_URL}/{self.slug}"

    @property
    def monto_abono_servicio(self):
        """Calcula el monto de abono para un servicio dado"""
        if self.monto_abono_fijo:
            return self.monto_abono_fijo
        return None  # Se calculará por servicio

    def get_horarios_disponibles(self, fecha):
        """
        Obtiene los horarios disponibles para una fecha específica
        RF-10: Horarios disponibles
        """
        # Implementación en la vista
        pass


class ConfiguracionHorario(models.Model):
    """
    Configuración de horarios por día de la semana
    Permite definir horarios diferentes para cada día
    """

    DIAS_SEMANA = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]

    negocio = models.ForeignKey(
        Negocio,
        on_delete=models.CASCADE,
        related_name='configuraciones_horario',
        verbose_name='Negocio'
    )
    dia_semana = models.IntegerField('Día de la semana', choices=DIAS_SEMANA)
    esta_abierto = models.BooleanField('Está abierto', default=True)
    hora_apertura = models.TimeField('Hora de apertura')
    hora_cierre = models.TimeField('Hora de cierre')

    class Meta:
        verbose_name = 'Configuración de horario'
        verbose_name_plural = 'Configuraciones de horario'
        unique_together = ('negocio', 'dia_semana')
        ordering = ['dia_semana']

    def __str__(self):
        return f"{self.negocio.nombre} - {self.get_dia_semana_display()}"


class BloqueoAgenda(models.Model):
    """
    RF-46, RF-47, RF-48: Bloqueo de horarios específicos
    """

    negocio = models.ForeignKey(
        Negocio,
        on_delete=models.CASCADE,
        related_name='bloqueos',
        verbose_name='Negocio'
    )
    fecha_inicio = models.DateTimeField('Fecha y hora de inicio')
    fecha_fin = models.DateTimeField('Fecha y hora de fin')
    motivo_interno = models.CharField(
        'Motivo interno',
        max_length=200,
        help_text='Este motivo solo lo ve el administrador'
    )
    esta_activo = models.BooleanField('Activo', default=True)
    fecha_creacion = models.DateTimeField('Fecha de creación', auto_now_add=True)

    class Meta:
        verbose_name = 'Bloqueo de agenda'
        verbose_name_plural = 'Bloqueos de agenda'
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"{self.negocio.nombre} - {self.fecha_inicio.strftime('%d/%m/%Y %H:%M')} - {self.motivo_interno}"
