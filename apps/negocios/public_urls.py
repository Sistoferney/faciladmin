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

    # Servicios
    path('<slug:slug>/admin/servicios/', admin_views.servicios_admin, name='admin_servicios'),
    path('<slug:slug>/admin/servicios/nuevo/', admin_views.servicio_crear, name='servicio_crear'),
    path('<slug:slug>/admin/servicios/<int:servicio_id>/editar/', admin_views.servicio_editar, name='servicio_editar'),
    path('<slug:slug>/admin/servicios/<int:servicio_id>/eliminar/', admin_views.servicio_eliminar, name='servicio_eliminar'),

    # Agenda y Citas
    path('<slug:slug>/admin/agenda/', admin_views.agenda_admin, name='admin_agenda'),
    path('<slug:slug>/admin/citas/<int:cita_id>/confirmar/', admin_views.cita_confirmar, name='cita_confirmar'),
    path('<slug:slug>/admin/citas/<int:cita_id>/completar/', admin_views.cita_completar, name='cita_completar'),
    path('<slug:slug>/admin/citas/<int:cita_id>/cancelar/', admin_views.cita_cancelar, name='cita_cancelar'),
    path('<slug:slug>/admin/citas/<int:cita_id>/no-asistio/', admin_views.cita_no_asistio, name='cita_no_asistio'),

    # Bloqueos de Horarios
    path('<slug:slug>/admin/bloqueos/', admin_views.bloqueos_admin, name='bloqueos_admin'),
    path('<slug:slug>/admin/bloqueos/nuevo/', admin_views.bloqueo_crear, name='bloqueo_crear'),
    path('<slug:slug>/admin/bloqueos/<int:bloqueo_id>/editar/', admin_views.bloqueo_editar, name='bloqueo_editar'),
    path('<slug:slug>/admin/bloqueos/<int:bloqueo_id>/eliminar/', admin_views.bloqueo_eliminar, name='bloqueo_eliminar'),

    # Abonos
    path('<slug:slug>/admin/abonos/', admin_views.abonos_admin, name='abonos_admin'),
    path('<slug:slug>/admin/abonos/<int:abono_id>/confirmar/', admin_views.abono_confirmar, name='abono_confirmar'),
    path('<slug:slug>/admin/abonos/<int:abono_id>/rechazar/', admin_views.abono_rechazar, name='abono_rechazar'),

    # Otros
    path('<slug:slug>/admin/clientes/', admin_views.clientes_admin, name='admin_clientes'),
    path('<slug:slug>/admin/configuracion/', admin_views.configuracion_admin, name='admin_configuracion'),

    # Mini página pública del negocio
    path('<slug:slug>/', public_views.minipagina_negocio, name='minipagina'),
    path('<slug:slug>/agendar/', public_views.agendar_cita, name='agendar'),
    path('<slug:slug>/confirmacion/<int:cita_id>/', public_views.confirmacion_cita, name='confirmacion_cita'),

    # API para disponibilidad
    path('<slug:slug>/api/disponibilidad/', public_views.disponibilidad_api, name='disponibilidad_api'),
    path('<slug:slug>/api/buscar-cliente/', public_views.buscar_cliente_api, name='buscar_cliente_api'),
]
