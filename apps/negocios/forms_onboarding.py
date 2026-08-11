"""
Formularios para el sistema de Onboarding Guiado
"""
from django import forms
from .models import Negocio


class DatosBasicosOnboardingForm(forms.ModelForm):
    """
    Formulario para el paso 1: Datos Básicos
    """
    class Meta:
        model = Negocio
        fields = ['nombre', 'tipo', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Ej: Spa Relax & Wellness',
                'autofocus': True
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select form-select-lg'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe tu negocio en pocas palabras. Ej: Spa especializado en tratamientos de relajación y bienestar con más de 10 años de experiencia.'
            }),
        }
        labels = {
            'nombre': '¿Cómo se llama tu negocio?',
            'tipo': '¿Qué tipo de negocio es?',
            'descripcion': 'Cuéntanos sobre tu negocio (opcional)',
        }


class IdentidadVisualOnboardingForm(forms.ModelForm):
    """
    Formulario para el paso 2: Identidad Visual
    """
    class Meta:
        model = Negocio
        fields = ['logo', 'imagen_portada', 'color_primario', 'color_secundario']
        widgets = {
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
        }
        labels = {
            'logo': 'Logo de tu negocio',
            'imagen_portada': 'Imagen de portada',
            'color_primario': 'Color principal de tu marca',
            'color_secundario': 'Color secundario',
        }
        help_texts = {
            'logo': 'Recomendado: 500x500px, formato PNG con fondo transparente',
            'imagen_portada': 'Recomendado: 1920x600px, formato JPG',
            'color_primario': 'Este color se usará en botones y elementos destacados',
            'color_secundario': 'Color complementario para detalles',
        }


class UbicacionContactoOnboardingForm(forms.ModelForm):
    """
    Formulario para el paso 3: Ubicación y Contacto
    """
    class Meta:
        model = Negocio
        fields = ['direccion', 'ciudad', 'estado', 'codigo_postal', 'telefono', 'email', 'whatsapp', 'es_a_domicilio']
        widgets = {
            'direccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Calle Principal #123, Colonia Centro'
            }),
            'ciudad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Ciudad de México'
            }),
            'estado': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: CDMX'
            }),
            'codigo_postal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 06000'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 555-1234-5678',
                'type': 'tel'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: contacto@tunegocio.com'
            }),
            'whatsapp': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 555-1234-5678',
                'type': 'tel'
            }),
            'es_a_domicilio': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'direccion': 'Dirección completa',
            'ciudad': 'Ciudad',
            'estado': 'Estado',
            'codigo_postal': 'Código Postal',
            'telefono': 'Teléfono de contacto',
            'email': 'Email de contacto (opcional)',
            'whatsapp': 'WhatsApp (opcional)',
            'es_a_domicilio': 'Ofrezco servicios a domicilio',
        }


class HorariosOnboardingForm(forms.ModelForm):
    """
    Formulario para el paso 4: Horarios de Atención
    """
    class Meta:
        model = Negocio
        fields = ['horario_apertura', 'horario_cierre', 'dias_atencion']
        widgets = {
            'horario_apertura': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'horario_cierre': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'dias_atencion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Lunes a Viernes, Lunes a Sábado'
            }),
        }
        labels = {
            'horario_apertura': '¿A qué hora abres?',
            'horario_cierre': '¿A qué hora cierras?',
            'dias_atencion': '¿Qué días atiendes?',
        }
        help_texts = {
            'horario_apertura': 'Hora de apertura general',
            'horario_cierre': 'Hora de cierre general',
            'dias_atencion': 'Puedes especificar días especiales en configuración avanzada',
        }
