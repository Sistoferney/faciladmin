"""
URLs públicas para mini página del negocio
RF-09, RF-11: Enlace único y reservas
"""
from django.urls import path

app_name = 'public'

urlpatterns = [
    # Mini página pública del negocio
    # path('<slug:slug>/', views.MiniPaginaNegocioView.as_view(), name='minipagina'),
    # path('<slug:slug>/agendar/', views.AgendarCitaView.as_view(), name='agendar'),
]
