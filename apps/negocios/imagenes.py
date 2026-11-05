"""
Logo y portada que suben los dueños

Aceptan la foto que tengan: aquí se endereza, se reduce y se comprime para que
la mini-página cargue rápido en el celular. Un PNG transparente lo sigue siendo.
"""
from io import BytesIO

from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile, UploadedFile
from PIL import Image, ImageOps

PESO_MAXIMO_MB = 15
LADO_LOGO = 800
LADO_PORTADA = 1920
TIPOS_ACEPTADOS = 'image/jpeg,image/png,image/webp'


def ajustar_imagen(archivo, lado_maximo, nombre):
    if archivo.size > PESO_MAXIMO_MB * 1024 * 1024:
        raise forms.ValidationError(f'La imagen no debe superar {PESO_MAXIMO_MB} MB.')

    try:
        archivo.seek(0)
        imagen = ImageOps.exif_transpose(Image.open(archivo))
        imagen.thumbnail((lado_maximo, lado_maximo), Image.Resampling.LANCZOS)

        salida = BytesIO()
        if imagen.mode in ('RGBA', 'LA', 'PA') or 'transparency' in imagen.info:
            imagen.convert('RGBA').save(salida, 'PNG', optimize=True)
            extension, tipo = 'png', 'image/png'
        else:
            imagen.convert('RGB').save(salida, 'JPEG', quality=85, optimize=True, progressive=True)
            extension, tipo = 'jpg', 'image/jpeg'
    except (OSError, ValueError, Image.DecompressionBombError):
        raise forms.ValidationError('No pudimos leer esta imagen. Intenta con otra foto.')

    return SimpleUploadedFile(f'{nombre}.{extension}', salida.getvalue(), content_type=tipo)


class ImagenesAjustadasMixin:
    """Para los formularios con logo y portada. Sin archivo nuevo no cambia nada."""

    def clean_logo(self):
        logo = self.cleaned_data.get('logo')
        if isinstance(logo, UploadedFile):
            return ajustar_imagen(logo, LADO_LOGO, 'logo')
        return logo

    def clean_imagen_portada(self):
        portada = self.cleaned_data.get('imagen_portada')
        if isinstance(portada, UploadedFile):
            return ajustar_imagen(portada, LADO_PORTADA, 'portada')
        return portada
