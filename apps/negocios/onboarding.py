"""
Sistema de Onboarding Guiado para FacilAdmin
Gestiona el proceso de configuración inicial del negocio
"""
from django.db import models
from django.utils import timezone


class OnboardingProgress(models.Model):
    """
    Modelo para trackear el progreso del onboarding del negocio
    """
    negocio = models.OneToOneField(
        'negocios.Negocio',
        on_delete=models.CASCADE,
        related_name='onboarding_progress'
    )

    # Progreso general (0-100)
    porcentaje_completado = models.IntegerField(default=0)

    # Timestamps de cada paso
    datos_basicos_completado = models.BooleanField(default=False)
    datos_basicos_fecha = models.DateTimeField(null=True, blank=True)

    identidad_visual_completado = models.BooleanField(default=False)
    identidad_visual_fecha = models.DateTimeField(null=True, blank=True)

    ubicacion_contacto_completado = models.BooleanField(default=False)
    ubicacion_contacto_fecha = models.DateTimeField(null=True, blank=True)

    horarios_completado = models.BooleanField(default=False)
    horarios_fecha = models.DateTimeField(null=True, blank=True)

    servicios_completado = models.BooleanField(default=False)
    servicios_fecha = models.DateTimeField(null=True, blank=True)

    # Control de onboarding
    onboarding_finalizado = models.BooleanField(default=False)
    fecha_finalizacion = models.DateTimeField(null=True, blank=True)
    onboarding_saltado = models.BooleanField(default=False)  # Si el usuario decidió saltarlo

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Progreso de Onboarding'
        verbose_name_plural = 'Progresos de Onboarding'

    def __str__(self):
        return f"{self.negocio.nombre} - {self.porcentaje_completado}%"

    def marcar_paso_completado(self, paso):
        """Marca un paso como completado y actualiza timestamp"""
        campo_completado = f"{paso}_completado"
        campo_fecha = f"{paso}_fecha"

        if hasattr(self, campo_completado):
            setattr(self, campo_completado, True)
            setattr(self, campo_fecha, timezone.now())
            self.calcular_progreso()
            self.save()

    def calcular_progreso(self):
        """Calcula el porcentaje de completitud basado en los pasos"""
        manager = OnboardingManager(self.negocio)
        self.porcentaje_completado = manager.calcular_progreso()

        # Si llegó al 100%, marcar como finalizado
        if self.porcentaje_completado >= 100 and not self.onboarding_finalizado:
            self.onboarding_finalizado = True
            self.fecha_finalizacion = timezone.now()

    def obtener_siguiente_paso(self):
        """Retorna el siguiente paso pendiente"""
        manager = OnboardingManager(self.negocio)
        return manager.siguiente_paso()


class OnboardingManager:
    """
    Gestiona la lógica del proceso de onboarding
    """

    # Definición de pasos del onboarding
    PASOS = {
        'datos_basicos': {
            'nombre': 'Datos Básicos',
            'descripcion': 'Nombre, tipo y descripción del negocio',
            'peso': 20,
            'requerido': True,
            'icono': 'bi-building',
            'campos': ['nombre', 'tipo', 'descripcion']
        },
        'identidad_visual': {
            'nombre': 'Identidad Visual',
            'descripcion': 'Logo, imagen de portada y colores',
            'peso': 25,
            'requerido': False,
            'icono': 'bi-palette',
            'campos': ['logo', 'imagen_portada']
        },
        'ubicacion_contacto': {
            'nombre': 'Ubicación y Contacto',
            'descripcion': 'Dirección, teléfono y redes sociales',
            'peso': 15,
            'requerido': False,
            'icono': 'bi-geo-alt',
            'campos': ['direccion', 'ciudad', 'telefono', 'email']
        },
        'horarios': {
            'nombre': 'Horarios de Atención',
            'descripcion': 'Configura cuándo está disponible tu negocio',
            'peso': 20,
            'requerido': False,
            'icono': 'bi-clock',
            'campos': ['horario_apertura', 'horario_cierre', 'dias_atencion']
        },
        'servicios': {
            'nombre': 'Servicios',
            'descripcion': 'Agrega al menos 3 servicios que ofreces',
            'peso': 20,
            'requerido': False,
            'icono': 'bi-scissors',
            'campos': ['servicios_minimos']
        }
    }

    def __init__(self, negocio):
        self.negocio = negocio
        self.progress, _ = OnboardingProgress.objects.get_or_create(negocio=negocio)

    def calcular_progreso(self):
        """Calcula el porcentaje total de completitud"""
        progreso_total = 0

        for paso_key, paso_config in self.PASOS.items():
            if self._paso_completado(paso_key):
                progreso_total += paso_config['peso']

        return min(progreso_total, 100)

    def _paso_completado(self, paso):
        """Verifica si un paso específico está completado"""
        config = self.PASOS.get(paso)
        if not config:
            return False

        campos = config['campos']

        # Caso especial: servicios_minimos
        if 'servicios_minimos' in campos:
            return self.negocio.servicios.count() >= 3

        # Verificar que todos los campos requeridos tengan valor
        for campo in campos:
            if campo == 'descripcion':  # Descripción es opcional
                continue
            valor = getattr(self.negocio, campo, None)
            if not valor:
                return False

        return True

    def siguiente_paso(self):
        """Retorna el siguiente paso pendiente"""
        for paso_key in self.PASOS.keys():
            if not self._paso_completado(paso_key):
                return paso_key
        return None

    def obtener_pasos_con_estado(self):
        """Retorna lista de pasos con su estado actual"""
        pasos_con_estado = []

        for paso_key, paso_config in self.PASOS.items():
            completado = self._paso_completado(paso_key)
            pasos_con_estado.append({
                'key': paso_key,
                'nombre': paso_config['nombre'],
                'descripcion': paso_config['descripcion'],
                'peso': paso_config['peso'],
                'icono': paso_config['icono'],
                'completado': completado,
                'requerido': paso_config['requerido']
            })

        return pasos_con_estado

    def saltar_onboarding(self):
        """Marca el onboarding como saltado"""
        self.progress.onboarding_saltado = True
        self.progress.save()

    def necesita_onboarding(self):
        """Determina si el usuario necesita ver el onboarding"""
        return (
            not self.progress.onboarding_finalizado and
            not self.progress.onboarding_saltado and
            self.progress.porcentaje_completado < 100
        )
