from django.contrib import admin
from django.utils.html import format_html
from .models import Cita


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = (
        'cliente',
        'servicio',
        'fecha_hora_display',
        'estado_display',
        'origen',
        'confirmada_por_admin',
        'abono_vencido_display'
    )
    list_filter = ('estado', 'origen', 'confirmada_por_admin', 'fecha_hora', 'negocio')
    search_fields = ('cliente__nombre', 'cliente__telefono', 'servicio__nombre')
    date_hierarchy = 'fecha_hora'
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'fecha_confirmacion', 'duracion_minutos')

    fieldsets = (
        ('Información de la Cita', {
            'fields': ('negocio', 'cliente', 'servicio', 'fecha_hora', 'duracion_minutos')
        }),
        ('Estado', {
            'fields': ('estado', 'origen', 'confirmada_por_admin', 'fecha_confirmacion')
        }),
        ('Abono', {
            'fields': ('fecha_limite_abono',),
            'classes': ('collapse',)
        }),
        ('Notas', {
            'fields': ('notas_cliente', 'notas_internas')
        }),
        ('Notificaciones', {
            'fields': ('recordatorio_enviado', 'confirmacion_enviada'),
            'classes': ('collapse',)
        }),
        ('Sistema', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

    def fecha_hora_display(self, obj):
        return obj.fecha_hora.strftime('%d/%m/%Y %H:%M')
    fecha_hora_display.short_description = 'Fecha y hora'

    def estado_display(self, obj):
        colores = {
            'pendiente_abono': '#ffc107',  # amarillo
            'confirmada': '#28a745',  # verde
            'completada': '#17a2b8',  # azul
            'cancelada': '#dc3545',  # rojo
            'no_asistio': '#6c757d',  # gris
        }
        color = colores.get(obj.estado, '#000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_display.short_description = 'Estado'

    def abono_vencido_display(self, obj):
        if obj.abono_vencido:
            return format_html('<span style="color: red; font-weight: bold;">⚠ VENCIDO</span>')
        return '-'
    abono_vencido_display.short_description = 'Abono'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Si el usuario no es superadmin, solo mostrar citas de su negocio
        if not request.user.is_superuser and hasattr(request.user, 'negocio'):
            qs = qs.filter(negocio=request.user.negocio)
        return qs

    actions = ['confirmar_citas', 'marcar_completadas', 'cancelar_citas']

    def confirmar_citas(self, request, queryset):
        for cita in queryset.filter(estado='pendiente_abono'):
            cita.confirmar_abono(request.user)
        self.message_user(request, f'{queryset.count()} citas confirmadas.')
    confirmar_citas.short_description = 'Confirmar abono de citas seleccionadas'

    def marcar_completadas(self, request, queryset):
        for cita in queryset.filter(estado='confirmada'):
            cita.marcar_completada()
        self.message_user(request, f'{queryset.count()} citas marcadas como completadas.')
    marcar_completadas.short_description = 'Marcar como completadas'

    def cancelar_citas(self, request, queryset):
        queryset.update(estado='cancelada')
        self.message_user(request, f'{queryset.count()} citas canceladas.')
    cancelar_citas.short_description = 'Cancelar citas seleccionadas'
