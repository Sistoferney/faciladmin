"""
Iconos de la marca (static/images/iconos), insertados como SVG para que tomen
el color del texto que los rodea.

Uso:
    {% load iconos %}
    {% icono 'agenda' %}                -> decorativo (lo ignoran los lectores de pantalla)
    {% icono 'buscar' 'fa-icon-lg' %}   -> con una clase extra
"""
import re
from functools import lru_cache

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()

CARPETA = settings.BASE_DIR / 'static' / 'images' / 'iconos'


@lru_cache(maxsize=None)
def _svg(nombre):
    if not re.fullmatch(r'[a-z0-9-]+', nombre):
        raise template.TemplateSyntaxError(f'Nombre de icono inválido: {nombre!r}')
    svg = (CARPETA / f'{nombre}.svg').read_text(encoding='utf-8').strip()
    # Tamaño por CSS (.fa-icon); oculto para lectores de pantalla
    return re.sub(r'<svg[^>]*?(viewBox="[^"]+")[^>]*>',
                  r'<svg class="fa-icon{clase}" \1 xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false">',
                  svg, count=1)


@register.simple_tag
def icono(nombre, clase=''):
    return mark_safe(_svg(nombre).replace('{clase}', f' {clase}' if clase else '', 1))
