"""
Template tags para enlaces de WhatsApp

Uso:
    {% load whatsapp %}
    {% whatsapp_negocio negocio "Hola, tengo una duda" %}   -> URL al negocio
    {% whatsapp_cliente_a_negocio cita %}                   -> cliente pregunta por su cita
    {% whatsapp_negocio_a_cliente cita %}                   -> dueño escribe al cliente
"""
from django import template

from apps.core import whatsapp

register = template.Library()


@register.simple_tag
def whatsapp_negocio(negocio, texto=''):
    return whatsapp.enlace_whatsapp(whatsapp.contacto_negocio(negocio), texto)


@register.simple_tag
def whatsapp_cliente_a_negocio(cita):
    return whatsapp.enlace_cliente_a_negocio(cita)


@register.simple_tag
def whatsapp_negocio_a_cliente(cita):
    return whatsapp.enlace_negocio_a_cliente(cita)


@register.simple_tag
def whatsapp_comprobante(cita):
    return whatsapp.enlace_comprobante(cita)
