"""
Modelos para reportes
RF-38, RF-39

Este módulo contiene servicios y vistas para generar reportes.
No requiere modelos adicionales, ya que usa los datos de Cita, Cliente, etc.
"""
from django.db import models


# Los reportes se generarán mediante vistas y servicios
# que consultan los modelos existentes (Cita, Cliente, Servicio)
# RF-38: Número de citas, clientes recurrentes, ingresos
# RF-39: Horarios con baja ocupación
