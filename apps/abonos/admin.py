from django.contrib import admin
from django.utils.html import format_html
from .models import Abono


@admin.register(Abono)
class AbonoAdmin(admin.ModelAdmin):
    list_display = (
        'cita',
        'monto_display',
        'metodo_pago',
        'estado_display',
        'fecha_limite',
        'dias_para_vencer_display',
        'confirmado_por'
    )
    list_filter = ('estado', 'metodo_pago', 'fecha_limite', 'fecha_creacion')
    search_fields = (
        'cita__cliente__nombre',
        'cita__cliente__telefono',
        'numero_referencia'
    )
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'fecha_confirmacion')
    date_hierarchy = 'fecha_limite'

    fieldsets = (
        ('Información del Abono', {
            'fields': ('cita', 'monto', 'metodo_pago', 'estado')
        }),
        ('Información de Pago', {
            'fields': ('numero_referencia', 'comprobante', 'fecha_pago')
        }),
        ('Fechas', {
            'fields': ('fecha_limite', 'fecha_confirmacion')
        }),
        ('Confirmación del Admin', {
            'fields': ('confirmado_por', 'notas_admin')
        }),
        ('Sistema', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

    def monto_display(self, obj):
        return f"${obj.monto:,.2f}"
    monto_display.short_description = 'Monto'
    monto_display.admin_order_field = 'monto'

    def estado_display(self, obj):
        colores = {
            'pendiente': '#ffc107',
            'confirmado': '#28a745',
            'rechazado': '#dc3545',
            'vencido': '#6c757d',
        }
        color = colores.get(obj.estado, '#000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_display.short_description = 'Estado'

    def dias_para_vencer_display(self, obj):
        if obj.estado != 'pendiente':
            return '-'

        dias = obj.dias_para_vencer
        if obj.esta_vencido:
            return format_html('<span style="color: red; font-weight: bold;">VENCIDO</span>')
        elif dias <= 1:
            return format_html('<span style="color: orange; font-weight: bold;">{} día</span>', dias)
        else:
            return f"{dias} días"
    dias_para_vencer_display.short_description = 'Días para vencer'

    def get_queryset(self, request):
        """Filtrar abonos por negocio del usuario"""
        qs = super().get_queryset(request)
        # Si el usuario tiene un negocio asociado, solo mostrar abonos de ese negocio
        if hasattr(request.user, 'negocio'):
            qs = qs.filter(cita__negocio=request.user.negocio)
        # Si no tiene negocio asociado, es superadmin del sistema y puede ver todos
        return qs

    actions = ['confirmar_abonos', 'rechazar_abonos']

    def confirmar_abonos(self, request, queryset):
        for abono in queryset.filter(estado='pendiente'):
            abono.confirmar(request.user)
        self.message_user(request, f'{queryset.count()} abonos confirmados.')
    confirmar_abonos.short_description = 'Confirmar abonos seleccionados'

    def rechazar_abonos(self, request, queryset):
        for abono in queryset.filter(estado='pendiente'):
            abono.rechazar(request.user, 'Rechazado desde panel de administración')
        self.message_user(request, f'{queryset.count()} abonos rechazados.')
    rechazar_abonos.short_description = 'Rechazar abonos seleccionados'
