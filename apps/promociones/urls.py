"""
URLs para API de promociones
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'promociones'

router = DefaultRouter()
# router.register(r'', views.PromocionViewSet, basename='promocion')

urlpatterns = [
    path('', include(router.urls)),
]
