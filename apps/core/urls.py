"""
URLs para vistas principales (landing, registro, etc.)
"""
from django.urls import path
from . import views, auth_views

app_name = 'core'

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('registro/', views.registro_negocio, name='registro'),
    path('precios/', views.precios, name='precios'),
    path('como-funciona/', views.como_funciona, name='como_funciona'),
    path('contacto/', views.contacto, name='contacto'),

    # Health check para monitoreo
    path('health/', views.health_check, name='health_check'),

    # Redirección después de login
    path('dashboard/', auth_views.redirect_after_login, name='dashboard_redirect'),
]
