"""
URLs para API REST de negocios
Las URLs de Onboarding están en urls_onboarding.py
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'negocios'

router = DefaultRouter()
# router.register(r'', views.NegocioViewSet, basename='negocio')
# router.register(r'bloqueos', views.BloqueoAgendaViewSet, basename='bloqueo')

urlpatterns = [
    # API REST
    path('', include(router.urls)),
]
