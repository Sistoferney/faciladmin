from django.contrib import admin
from django.utils.html import format_html
from .models import Promocion


@admin.register(Promocion)
class PromocionAdmin(admin.ModelAdmin):
    list_display = (
        'nombre',
        'negocio',
        'segmento',
        'estado_display',
        'total_destinatarios',
        'total_enviados',
        'fecha_envio'
    )
    list_filter = ('estado', 'segmento', 'fecha_creacion', 'negocio')
    search_fields = ('nombre', 'descripcion', 'codigo_descuento')
    readonly_fields = (
        'total_destinatarios',
        'total_enviados',
        'total_fallidos',
        'fecha_envio',
        'fecha_creacion',
        'fecha_actualizacion'
    )

    fieldsets = (
        ('Información Básica', {
            'fields': ('negocio', 'nombre', 'descripcion', 'mensaje')
        }),
        ('Segmentación', {
            'fields': ('segmento',)
        }),
        ('Configuración de Descuento', {
            'fields': ('codigo_descuento', 'porcentaje_descuento', 'imagen')
        }),
        ('Programación', {
            'fields': ('fecha_inicio', 'fecha_fin')
        }),
        ('Estado', {
            'fields': ('estado',)
        }),
        ('Estadísticas', {
            'fields': ('total_destinatarios', 'total_enviados', 'total_fallidos', 'fecha_envio'),
            'classes': ('collapse',)
        }),
        ('Sistema', {
            'fields': ('creado_por', 'fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

    def estado_display(self, obj):
        colores = {
            'borrador': '#6c757d',
            'programada': '#ffc107',
            'enviada': '#28a745',
            'finalizada': '#17a2b8',
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
        # Si el usuario no es superadmin, solo mostrar promociones de su negocio
        if not request.user.is_superuser and hasattr(request.user, 'negocio'):
            qs = qs.filter(negocio=request.user.negocio)
        return qs

    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo objeto
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)

    actions = ['enviar_promociones']

    def enviar_promociones(self, request, queryset):
        total_enviados = 0
        for promocion in queryset.filter(estado__in=['borrador', 'programada']):
            resultado = promocion.enviar_campana()
            total_enviados += resultado['enviados']

        self.message_user(
            request,
            f'Enviadas {total_enviados} promociones a los clientes.'
        )
    enviar_promociones.short_description = 'Enviar promociones seleccionadas'
