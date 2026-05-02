"""
URLs para API de clientes
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'clientes'

router = DefaultRouter()
# router.register(r'', views.ClienteViewSet, basename='cliente')

urlpatterns = [
    path('', include(router.urls)),
]
