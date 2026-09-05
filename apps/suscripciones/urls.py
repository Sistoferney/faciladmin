from django.urls import path
from . import views

app_name = 'suscripciones'

urlpatterns = [
    # Registro
    path('registro/', views.registro_negocio, name='registro_negocio'),
    path('registro/pendiente/', views.registro_pendiente, name='registro_pendiente'),
    path('validar/<str:token>/', views.validar_email, name='validar_email'),

    # Programa de Referidos
    path('programa-referidos/', views.programa_referidos_dashboard, name='programa_referidos'),
    path('programa-referidos/agregar/', views.agregar_referido_ajax, name='agregar_referido'),
    path('programa-referidos/generar-cupon/', views.generar_cupon_referidos, name='generar_cupon_referidos'),

    # Canje de Cupones
    path('canjear-cupon/', views.canjear_cupon, name='canjear_cupon'),
]
