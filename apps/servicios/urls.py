"""
URLs para API de servicios
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'servicios'

router = DefaultRouter()
# router.register(r'', views.ServicioViewSet, basename='servicio')

urlpatterns = [
    path('', include(router.urls)),
]
