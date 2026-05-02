"""
Formularios para registro de negocios
"""
from django import forms
from apps.authentication.models import Usuario
from apps.negocios.models import Negocio


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
            'placeholder': '+52 55 1234 5678'
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
            'placeholder': '+52 55 9876 5432'
        })
    )
    ciudad = forms.CharField(
        max_length=100,
        label='Ciudad',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Ciudad de México'
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
