"""
Uso: {% load formato %} ... {{ cita.saldo_pendiente|pesos }} -> $30.000
"""
from django import template

from apps.core.formato import pesos as formatear_pesos

register = template.Library()


@register.filter
def pesos(valor):
    return formatear_pesos(valor)
