"""
Formularios para gestión de negocios
"""
from django import forms
from .models import Negocio, BloqueoAgenda
from apps.servicios.models import Servicio


class ConfiguracionNegocioForm(forms.ModelForm):
    """
    Formulario para que el admin del negocio configure su mini-página
    """
    # Checkboxes para días laborables
    dia_lunes = forms.BooleanField(required=False, label='Lunes')
    dia_martes = forms.BooleanField(required=False, label='Martes')
    dia_miercoles = forms.BooleanField(required=False, label='Miércoles')
    dia_jueves = forms.BooleanField(required=False, label='Jueves')
    dia_viernes = forms.BooleanField(required=False, label='Viernes')
    dia_sabado = forms.BooleanField(required=False, label='Sábado')
    dia_domingo = forms.BooleanField(required=False, label='Domingo')

    class Meta:
        model = Negocio
        fields = [
            # Información básica
            'nombre',
            'tipo',
            'descripcion',
            'telefono',
            'email',
            'whatsapp',

            # Dirección
            'direccion',
            'ciudad',
            'estado',
            'codigo_postal',

            # Tipo de servicio
            'es_a_domicilio',

            # Horarios
            'horario_apertura',
            'horario_cierre',

            # Personalización
            'logo',
            'imagen_portada',
            'color_primario',
            'color_secundario',

            # Redes sociales
            'facebook',
            'instagram',
            'twitter',

            # Configuración de abonos
            'requiere_abono',
            'porcentaje_abono',
            'monto_abono_fijo',
            'banco',
            'numero_cuenta',
            'clabe',
            'titular_cuenta',

            # Estado
            'esta_activo',
            'acepta_reservas_online',
        ]

        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de tu negocio'
            }),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe brevemente tu negocio...'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+57 XXX XXX XXXX'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
            'whatsapp': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+57 XXX XXX XXXX'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Calle y número'
            }),
            'ciudad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ciudad'
            }),
            'estado': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Estado'
            }),
            'codigo_postal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'C.P.'
            }),
            'es_a_domicilio': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'horario_apertura': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'horario_cierre': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'imagen_portada': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'color_primario': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'color_secundario': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'facebook': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://facebook.com/tu-pagina'
            }),
            'instagram': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://instagram.com/tu-usuario'
            }),
            'twitter': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://twitter.com/tu-usuario'
            }),
            'requiere_abono': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'porcentaje_abono': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01'
            }),
            'monto_abono_fijo': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01'
            }),
            'banco': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del banco'
            }),
            'numero_cuenta': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de cuenta'
            }),
            'clabe': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Confirma el número de cuenta'
            }),
            'titular_cuenta': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del titular'
            }),
            'esta_activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'acepta_reservas_online': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

        labels = {
            'nombre': 'Nombre del Negocio',
            'tipo': 'Tipo de Negocio',
            'descripcion': 'Descripción',
            'telefono': 'Teléfono',
            'email': 'Email',
            'whatsapp': 'WhatsApp',
            'direccion': 'Dirección',
            'ciudad': 'Ciudad',
            'estado': 'Estado',
            'codigo_postal': 'Código Postal',
            'es_a_domicilio': 'Servicio a Domicilio',
            'horario_apertura': 'Hora de Apertura',
            'horario_cierre': 'Hora de Cierre',
            'logo': 'Logo (500x500 px recomendado)',
            'imagen_portada': 'Imagen de Portada (1920x600 px recomendado)',
            'color_primario': 'Color Primario',
            'color_secundario': 'Color Secundario',
            'facebook': 'Facebook',
            'instagram': 'Instagram',
            'twitter': 'Twitter',
            'requiere_abono': 'Requiere Abono para Reservar',
            'porcentaje_abono': 'Porcentaje de Abono (%)',
            'monto_abono_fijo': 'Monto Fijo de Abono ($)',
            'banco': 'Banco',
            'numero_cuenta': 'Número de Cuenta',
            'clabe': 'Confirmar Número de Cuenta',
            'titular_cuenta': 'Titular de la Cuenta',
            'esta_activo': 'Negocio Activo',
            'acepta_reservas_online': 'Acepta Reservas Online',
        }

        help_texts = {
            'descripcion': 'Describe brevemente tu negocio y servicios',
            'es_a_domicilio': 'Marcar si ofreces servicios a domicilio (sin local fijo). Se solicitará la dirección del cliente al agendar.',
            'logo': 'Formato: PNG (transparente recomendado) o JPG. Tamaño: 500x500 px. Peso máximo: 500 KB',
            'imagen_portada': 'Formato: JPG o PNG. Tamaño: 1920x600 px. Peso máximo: 1 MB',
            'color_primario': 'Color principal de tu marca (botones, enlaces)',
            'color_secundario': 'Color secundario (textos, bordes)',
            'requiere_abono': 'Marcar si deseas que los clientes paguen un abono al reservar',
            'porcentaje_abono': 'Porcentaje del servicio que se requiere como abono',
            'monto_abono_fijo': 'O define un monto fijo en lugar del porcentaje',
            'clabe': 'Vuelve a escribir el número de cuenta para confirmar que esté correcto',
            'esta_activo': 'Si está desactivado, tu mini-página no será visible',
            'acepta_reservas_online': 'Si está desactivado, no se podrán hacer reservas desde la web',
        }

    def __init__(self, *args, **kwargs):
        """Cargar estado actual de días laborables desde ConfiguracionHorario"""
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            from .models import ConfiguracionHorario

            # Mapeo de días
            dias_map = {
                0: 'dia_lunes',
                1: 'dia_martes',
                2: 'dia_miercoles',
                3: 'dia_jueves',
                4: 'dia_viernes',
                5: 'dia_sabado',
                6: 'dia_domingo',
            }

            # Cargar configuraciones existentes
            for dia_num, field_name in dias_map.items():
                config = ConfiguracionHorario.objects.filter(
                    negocio=self.instance,
                    dia_semana=dia_num
                ).first()

                if config:
                    # Si existe configuración, usar su valor
                    self.fields[field_name].initial = config.esta_abierto
                else:
                    # Si no existe, por defecto todos abiertos excepto domingo
                    self.fields[field_name].initial = (dia_num != 6)

    def save(self, commit=True):
        """Guardar negocio y crear/actualizar ConfiguracionHorario"""
        instance = super().save(commit=commit)

        if commit:
            from .models import ConfiguracionHorario
            from datetime import time

            # Mapeo de días
            dias_map = {
                0: self.cleaned_data.get('dia_lunes', True),
                1: self.cleaned_data.get('dia_martes', True),
                2: self.cleaned_data.get('dia_miercoles', True),
                3: self.cleaned_data.get('dia_jueves', True),
                4: self.cleaned_data.get('dia_viernes', True),
                5: self.cleaned_data.get('dia_sabado', True),
                6: self.cleaned_data.get('dia_domingo', False),
            }

            # Obtener horarios del negocio
            hora_apertura = instance.horario_apertura or time(9, 0)
            hora_cierre = instance.horario_cierre or time(19, 0)

            # Crear o actualizar configuración para cada día
            for dia_num, esta_abierto in dias_map.items():
                ConfiguracionHorario.objects.update_or_create(
                    negocio=instance,
                    dia_semana=dia_num,
                    defaults={
                        'esta_abierto': esta_abierto,
                        'hora_apertura': hora_apertura,
                        'hora_cierre': hora_cierre,
                    }
                )

        return instance

    def clean(self):
        """Validar horarios de apertura y cierre, y confirmación de número de cuenta"""
        cleaned_data = super().clean()
        hora_apertura = cleaned_data.get('horario_apertura')
        hora_cierre = cleaned_data.get('horario_cierre')
        numero_cuenta = cleaned_data.get('numero_cuenta')
        clabe = cleaned_data.get('clabe')

        # Validar horarios
        if hora_apertura and hora_cierre:
            if hora_cierre <= hora_apertura:
                raise forms.ValidationError(
                    'El horario de cierre debe ser posterior al horario de apertura.'
                )

        # Validar que el número de cuenta y su confirmación coincidan
        if numero_cuenta and clabe:
            # Limpiar espacios en blanco
            numero_cuenta_limpio = numero_cuenta.strip()
            clabe_limpio = clabe.strip()

            if numero_cuenta_limpio != clabe_limpio:
                self.add_error('clabe', 'Los números de cuenta no coinciden. Por favor verifica.')

        return cleaned_data


class ServicioForm(forms.ModelForm):
    """
    Formulario para crear y editar servicios desde el dashboard del cliente
    """
    class Meta:
        model = Servicio
        fields = [
            'nombre',
            'descripcion',
            'precio',
            'duracion_minutos',
            'frecuencia_dias',
            'imagen',
            'orden',
            'esta_activo',
            'requiere_contacto_directo',
            'requiere_abono',
            'monto_abono',
            'porcentaje_abono',
        ]

        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Corte de cabello, Manicure, Masaje relajante'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe el servicio, qué incluye, beneficios...'
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'duracion_minutos': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '5',
                'max': '360',
                'step': '5',
                'placeholder': '60'
            }),
            'frecuencia_dias': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': '30'
            }),
            'imagen': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'orden': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
            'esta_activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requiere_contacto_directo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requiere_abono': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'monto_abono': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'porcentaje_abono': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01',
                'placeholder': '0'
            }),
        }

        labels = {
            'nombre': 'Nombre del Servicio',
            'descripcion': 'Descripción',
            'precio': 'Precio ($)',
            'duracion_minutos': 'Duración (minutos)',
            'frecuencia_dias': 'Frecuencia Sugerida (días)',
            'imagen': 'Imagen del Servicio',
            'orden': 'Orden de Visualización',
            'esta_activo': 'Servicio Activo',
            'requiere_contacto_directo': 'Requiere Coordinación Directa',
            'requiere_abono': 'Requiere Abono Específico',
            'monto_abono': 'Monto Fijo de Abono ($)',
            'porcentaje_abono': 'Porcentaje de Abono (%)',
        }

        help_texts = {
            'nombre': 'Nombre del servicio que aparecerá en la mini-página',
            'descripcion': 'Descripción detallada del servicio',
            'precio': 'Precio del servicio en tu moneda local',
            'duracion_minutos': 'Duración aproximada del servicio (5-360 minutos / máx. 6 horas)',
            'frecuencia_dias': 'Cada cuántos días se recomienda repetir este servicio (opcional)',
            'imagen': 'Imagen que representa el servicio (opcional, 800x600 px recomendado)',
            'orden': 'Número para ordenar los servicios (menor número aparece primero)',
            'esta_activo': 'Si está desactivado, el servicio no será visible en la mini-página',
            'requiere_contacto_directo': 'Marcar si este servicio requiere contactar directamente para coordinar (ej: servicios a domicilio). Los clientes serán redirigidos a WhatsApp/llamada en lugar de agendar directamente.',
            'requiere_abono': 'Marcar si este servicio requiere un abono diferente al configurado para el negocio',
            'monto_abono': 'Monto fijo de abono para este servicio (deja vacío si usas porcentaje)',
            'porcentaje_abono': 'Porcentaje del precio como abono (deja vacío si usas monto fijo)',
        }

    def clean_duracion_minutos(self):
        """Validar duración del servicio"""
        duracion = self.cleaned_data.get('duracion_minutos')

        if duracion is not None:
            if duracion < 5:
                raise forms.ValidationError('La duración mínima es de 5 minutos.')
            if duracion > 360:
                raise forms.ValidationError('La duración máxima es de 360 minutos (6 horas). Los servicios no pueden exceder este tiempo.')

        return duracion


class BloqueoAgendaForm(forms.ModelForm):
    """
    Formulario para bloquear horarios en la agenda
    """
    class Meta:
        model = BloqueoAgenda
        fields = [
            'fecha_inicio',
            'fecha_fin',
            'motivo_interno',
            'esta_activo',
        ]

        widgets = {
            'fecha_inicio': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }),
            'fecha_fin': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }),
            'motivo_interno': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Vacaciones, Mantenimiento, Evento privado'
            }),
            'esta_activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

        labels = {
            'fecha_inicio': 'Fecha y Hora de Inicio',
            'fecha_fin': 'Fecha y Hora de Fin',
            'motivo_interno': 'Motivo del Bloqueo',
            'esta_activo': 'Bloqueo Activo',
        }

        help_texts = {
            'fecha_inicio': 'Fecha y hora desde la cual comienza el bloqueo',
            'fecha_fin': 'Fecha y hora hasta la cual termina el bloqueo',
            'motivo_interno': 'Motivo del bloqueo (solo visible para ti)',
            'esta_activo': 'Si está desactivado, el bloqueo no afectará la disponibilidad',
        }

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')

        if fecha_inicio and fecha_fin:
            if fecha_fin <= fecha_inicio:
                raise forms.ValidationError(
                    'La fecha de fin debe ser posterior a la fecha de inicio.'
                )

        return cleaned_data

# Importar formularios de onboarding
from .forms_onboarding import (
    DatosBasicosOnboardingForm,
    IdentidadVisualOnboardingForm,
    UbicacionContactoOnboardingForm,
    HorariosOnboardingForm,
)
