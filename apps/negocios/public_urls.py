"""
URLs públicas y de administración para mini página del negocio
RF-09, RF-11: Enlace único y reservas
"""
from django.urls import path
from . import public_views, admin_views

app_name = 'public'

urlpatterns = [
    # Panel de administración del negocio
    path('<slug:slug>/admin/', admin_views.dashboard_admin, name='admin_dashboard'),
    path('<slug:slug>/admin/servicios/', admin_views.servicios_admin, name='admin_servicios'),
    path('<slug:slug>/admin/agenda/', admin_views.agenda_admin, name='admin_agenda'),
    path('<slug:slug>/admin/clientes/', admin_views.clientes_admin, name='admin_clientes'),
    path('<slug:slug>/admin/abonos/', admin_views.abonos_admin, name='admin_abonos'),
    path('<slug:slug>/admin/configuracion/', admin_views.configuracion_admin, name='admin_configuracion'),

    # Mini página pública del negocio
    path('<slug:slug>/', public_views.minipagina_negocio, name='minipagina'),
    path('<slug:slug>/agendar/', public_views.agendar_cita, name='agendar'),
    path('<slug:slug>/confirmacion/<int:cita_id>/', public_views.confirmacion_cita, name='confirmacion_cita'),

    # API para disponibilidad
    path('<slug:slug>/api/disponibilidad/', public_views.disponibilidad_api, name='disponibilidad_api'),
]
