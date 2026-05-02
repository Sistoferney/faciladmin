from django.contrib import admin
from django.utils.html import format_html
from .models import Notificacion


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
        qs = super().get_queryset(request)
        # Si el usuario no es superadmin, solo mostrar notificaciones de su negocio
        if not request.user.is_superuser and hasattr(request.user, 'negocio'):
            qs = qs.filter(cliente__negocio=request.user.negocio)
        return qs

    actions = ['reenviar_notificaciones']

    def reenviar_notificaciones(self, request, queryset):
        for notificacion in queryset:
            notificacion.enviar()
        self.message_user(request, f'{queryset.count()} notificaciones reenviadas.')
    reenviar_notificaciones.short_description = 'Reenviar notificaciones seleccionadas'
