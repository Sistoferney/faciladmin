"""
URLs para API REST de negocios
Las URLs de Onboarding están en urls_onboarding.py
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# app_name removido para evitar colisión con namespace 'negocios' de urls_onboarding
# Si se necesitan endpoints API en el futuro, usar namespace 'api_negocios'

router = DefaultRouter()
# router.register(r'', views.NegocioViewSet, basename='negocio')
# router.register(r'bloqueos', views.BloqueoAgendaViewSet, basename='bloqueo')

urlpatterns = [
    # API REST
    path('', include(router.urls)),
]
