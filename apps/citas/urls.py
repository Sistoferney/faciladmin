"""
URLs para API de citas
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'citas'

router = DefaultRouter()
# router.register(r'', views.CitaViewSet, basename='cita')

urlpatterns = [
    path('', include(router.urls)),
    # path('disponibilidad/', views.DisponibilidadView.as_view(), name='disponibilidad'),
]
