from django.contrib import admin
from django.utils.html import format_html
from .models import Notificacion, ClientePushSubscription


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = (
        'cliente',
        'tipo',
        'canal',
        'estado_display',
        'fecha_envio',
        'fecha_creacion'
    )
    list_filter = ('tipo', 'canal', 'estado', 'fecha_creacion', 'fecha_envio')
    search_fields = ('cliente__nombre', 'cliente__telefono', 'mensaje', 'asunto')
    readonly_fields = ('fecha_creacion', 'fecha_envio', 'id_externo')
    date_hierarchy = 'fecha_creacion'

    fieldsets = (
        ('Destinatario', {
            'fields': ('cliente', 'cita')
        }),
        ('Configuración', {
            'fields': ('tipo', 'canal', 'estado')
        }),
        ('Contenido', {
            'fields': ('asunto', 'mensaje')
        }),
        ('Programación', {
            'fields': ('fecha_programada', 'fecha_envio')
        }),
        ('Respuesta del Servicio', {
            'fields': ('id_externo', 'error'),
            'classes': ('collapse',)
        }),
        ('Sistema', {
            'fields': ('fecha_creacion',),
            'classes': ('collapse',)
        }),
    )

    def estado_display(self, obj):
        colores = {
            'pendiente': '#ffc107',
            'enviada': '#28a745',
            'fallida': '#dc3545',
        }
        color = colores.get(obj.estado, '#000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_display.short_description = 'Estado'

    def get_queryset(self, request):
        """Filtrar notificaciones por negocio del usuario"""
        qs = super().get_queryset(request)
        # Si el usuario tiene un negocio asociado, solo mostrar notificaciones de ese negocio
        if hasattr(request.user, 'negocio'):
            qs = qs.filter(cliente__negocio=request.user.negocio)
        # Si no tiene negocio asociado, es superadmin del sistema y puede ver todos
        return qs

    actions = ['reenviar_notificaciones']

    def reenviar_notificaciones(self, request, queryset):
        for notificacion in queryset:
            notificacion.enviar()
        self.message_user(request, f'{queryset.count()} notificaciones reenviadas.')
    reenviar_notificaciones.short_description = 'Reenviar notificaciones seleccionadas'


@admin.register(ClientePushSubscription)
class ClientePushSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'cliente',
        'activa_display',
        'fecha_suscripcion',
        'user_agent_corto'
    )
    list_filter = ('activa', 'fecha_suscripcion')
    search_fields = ('cliente__nombre', 'cliente__telefono', 'endpoint')
    readonly_fields = ('fecha_suscripcion', 'fecha_actualizacion', 'endpoint', 'auth', 'p256dh')
    date_hierarchy = 'fecha_suscripcion'

    fieldsets = (
        ('Cliente', {
            'fields': ('cliente', 'activa')
        }),
        ('Información de Suscripción', {
            'fields': ('endpoint', 'auth', 'p256dh')
        }),
        ('Metadata', {
            'fields': ('user_agent', 'fecha_suscripcion', 'fecha_actualizacion')
        }),
    )

    def activa_display(self, obj):
        if obj.activa:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✓ Activa</span>'
            )
        else:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">✗ Inactiva</span>'
            )
    activa_display.short_description = 'Estado'

    def user_agent_corto(self, obj):
        if not obj.user_agent:
            return '-'
        # Mostrar solo los primeros 50 caracteres
        ua = obj.user_agent[:50]
        return ua + '...' if len(obj.user_agent) > 50 else ua
    user_agent_corto.short_description = 'User Agent'

    def get_queryset(self, request):
        """Filtrar suscripciones por negocio del usuario"""
        qs = super().get_queryset(request)
        # Si el usuario tiene un negocio asociado, solo mostrar suscripciones de ese negocio
        if hasattr(request.user, 'negocio'):
            qs = qs.filter(cliente__negocio=request.user.negocio)
        # Si no tiene negocio asociado, es superadmin del sistema y puede ver todos
        return qs

    actions = ['desactivar_suscripciones']

    def desactivar_suscripciones(self, request, queryset):
        count = queryset.update(activa=False)
        self.message_user(request, f'{count} suscripciones desactivadas.')
    desactivar_suscripciones.short_description = 'Desactivar suscripciones seleccionadas'
