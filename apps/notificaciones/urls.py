"""
URLs para API de notificaciones
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'notificaciones'

router = DefaultRouter()
# router.register(r'', views.NotificacionViewSet, basename='notificacion')

urlpatterns = [
    path('', include(router.urls)),
]
