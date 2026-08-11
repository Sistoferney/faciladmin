"""
URLs para API de negocios (admin) y Onboarding
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_onboarding

app_name = 'negocios'

router = DefaultRouter()
# router.register(r'', views.NegocioViewSet, basename='negocio')
# router.register(r'bloqueos', views.BloqueoAgendaViewSet, basename='bloqueo')

urlpatterns = [
    # Onboarding
    path('onboarding/', views_onboarding.onboarding_dashboard, name='onboarding_dashboard'),
    path('onboarding/datos-basicos/', views_onboarding.onboarding_paso_datos_basicos, name='onboarding_paso_datos_basicos'),
    path('onboarding/identidad-visual/', views_onboarding.onboarding_paso_identidad_visual, name='onboarding_paso_identidad_visual'),
    path('onboarding/ubicacion-contacto/', views_onboarding.onboarding_paso_ubicacion_contacto, name='onboarding_paso_ubicacion_contacto'),
    path('onboarding/horarios/', views_onboarding.onboarding_paso_horarios, name='onboarding_paso_horarios'),
    path('onboarding/servicios/', views_onboarding.onboarding_paso_servicios, name='onboarding_paso_servicios'),
    path('onboarding/saltar/', views_onboarding.onboarding_saltar, name='onboarding_saltar'),
    path('onboarding/completar/', views_onboarding.onboarding_completar, name='onboarding_completar'),

    # API REST
    path('', include(router.urls)),
]
