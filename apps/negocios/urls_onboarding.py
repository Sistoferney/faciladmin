"""
URLs para el sistema de Onboarding Guiado (vistas HTML)
Estas URLs están separadas de la API REST
El namespace 'negocios' se define en config/urls.py al incluir este archivo
"""
from django.urls import path
from . import views_onboarding

urlpatterns = [
    # Dashboard principal de onboarding
    path('onboarding/', views_onboarding.onboarding_dashboard, name='onboarding_dashboard'),

    # Pasos del onboarding
    path('onboarding/datos-basicos/', views_onboarding.onboarding_paso_datos_basicos, name='onboarding_paso_datos_basicos'),
    path('onboarding/identidad-visual/', views_onboarding.onboarding_paso_identidad_visual, name='onboarding_paso_identidad_visual'),
    path('onboarding/ubicacion-contacto/', views_onboarding.onboarding_paso_ubicacion_contacto, name='onboarding_paso_ubicacion_contacto'),
    path('onboarding/horarios/', views_onboarding.onboarding_paso_horarios, name='onboarding_paso_horarios'),
    path('onboarding/servicios/', views_onboarding.onboarding_paso_servicios, name='onboarding_paso_servicios'),

    # Acciones del onboarding
    path('onboarding/saltar/', views_onboarding.onboarding_saltar, name='onboarding_saltar'),
    path('onboarding/completar/', views_onboarding.onboarding_completar, name='onboarding_completar'),
]
