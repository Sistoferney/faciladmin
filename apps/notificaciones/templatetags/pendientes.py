"""
Uso: {% load pendientes %} {% pendientes_abiertos negocio as total %}
"""
from django import template

register = template.Library()


@register.simple_tag
def pendientes_abiertos(negocio):
    from apps.notificaciones.models import Pendiente
    return Pendiente.objects.filter(negocio=negocio, resuelto=False).count()
