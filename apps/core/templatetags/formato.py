"""
Uso: {% load formato %} ... {{ cita.saldo_pendiente|pesos }} -> $30.000
"""
from django import template

from apps.core.formato import pesos as formatear_pesos

register = template.Library()


@register.filter
def pesos(valor):
    return formatear_pesos(valor)


@register.filter
def iniciales(nombre):
    """'Aurora Estudio' -> 'AE' (avatar del negocio o de la persona)"""
    palabras = [p for p in str(nombre or '').split() if p[:1].isalnum()]
    return ''.join(p[0] for p in palabras[:2]).upper()
