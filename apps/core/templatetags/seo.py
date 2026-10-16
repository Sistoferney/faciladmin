"""
Datos estructurados (JSON-LD) para buscadores. Ver apps/core/seo.py
"""
from django import template
from django.templatetags.static import static

from apps.core import seo

register = template.Library()


@register.simple_tag(takes_context=True)
def datos_estructurados_plataforma(context):
    base = seo.url_base(context['request'])
    return seo.json_ld(seo.datos_plataforma(base, f"{base}{static('images/facilacces-logo.png')}"))


@register.simple_tag(takes_context=True)
def datos_estructurados_negocio(context, negocio):
    return seo.json_ld(seo.datos_negocio(negocio, seo.url_base(context['request'])))
