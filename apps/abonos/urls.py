"""
URLs para API de abonos
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'abonos'

router = DefaultRouter()
# router.register(r'', views.AbonoViewSet, basename='abono')

urlpatterns = [
    path('', include(router.urls)),
]
