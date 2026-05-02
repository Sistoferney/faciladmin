"""
URLs para API de negocios (admin)
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'negocios'

router = DefaultRouter()
# router.register(r'', views.NegocioViewSet, basename='negocio')
# router.register(r'bloqueos', views.BloqueoAgendaViewSet, basename='bloqueo')

urlpatterns = [
    path('', include(router.urls)),
]
