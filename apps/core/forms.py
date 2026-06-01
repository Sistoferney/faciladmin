"""
Formularios para registro de negocios
"""
from django import forms
from django.utils.text import slugify
from apps.authentication.models import Usuario
from apps.negocios.models import Negocio, SLUGS_RESERVADOS


class RegistroNegocioForm(forms.Form):
    """
    Formulario para registro de nuevo negocio (spa/peluquería)
    """
    # Datos del administrador
    nombre_admin = forms.CharField(
        max_length=255,
        label='Tu nombre completo',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Juan Pérez'
        })
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'tu@email.com'
        })
    )
    telefono_admin = forms.CharField(
        max_length=20,
        label='Tu teléfono',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+57 300 123 4567'
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mínimo 8 caracteres'
        })
    )
    password_confirm = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repite tu contraseña'
        })
    )

    # Datos del negocio
    nombre_negocio = forms.CharField(
        max_length=200,
        label='Nombre de tu negocio',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Spa Relax'
        })
    )
    tipo_negocio = forms.ChoiceField(
        choices=Negocio.TIPO_NEGOCIO_CHOICES,
        label='Tipo de negocio',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    telefono_negocio = forms.CharField(
        max_length=20,
        label='Teléfono del negocio',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+57 300 987 6543'
        })
    )
    ciudad = forms.CharField(
        max_length=100,
        label='Ciudad',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Bogotá'
        })
    )

    # Términos
    acepta_terminos = forms.BooleanField(
        required=True,
        label='Acepto los términos y condiciones',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm:
            if password != password_confirm:
                raise forms.ValidationError('Las contraseñas no coinciden')

            if len(password) < 8:
                raise forms.ValidationError('La contraseña debe tener al menos 8 caracteres')

        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError('Este email ya está registrado')
        return email

    def clean_nombre_negocio(self):
        nombre = self.cleaned_data.get('nombre_negocio')
        # Generar el slug que se usaría
        slug = slugify(nombre)

        # Verificar si el slug estaría en la lista de palabras reservadas
        if slug.lower() in SLUGS_RESERVADOS:
            raise forms.ValidationError(
                f'El nombre "{nombre}" genera una URL reservada del sistema. '
                'Por favor elige otro nombre para tu negocio. '
                'Nombres reservados: admin, login, api, etc.'
            )

        return nombre
