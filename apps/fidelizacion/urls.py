"""
URLs para fidelización
"""
from django.urls import path

app_name = 'fidelizacion'

urlpatterns = [
    # Esta app principalmente usa tareas de Celery
    # No requiere endpoints propios por ahora
]
