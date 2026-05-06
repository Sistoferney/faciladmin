from django.contrib import admin
from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'negocio', 'tipo_cliente', 'total_citas', 'total_gastado', 'ultima_visita', 'esta_activo')
    list_filter = ('tipo_cliente', 'esta_activo', 'acepta_promociones', 'fecha_registro', 'negocio')
    search_fields = ('nombre', 'telefono', 'email')
    readonly_fields = ('total_citas', 'total_gastado', 'ultima_visita', 'fecha_registro', 'fecha_actualizacion')

    fieldsets = (
        ('Información Básica', {
            'fields': ('negocio', 'nombre', 'telefono', 'email', 'fecha_nacimiento')
        }),
        ('Clasificación', {
            'fields': ('tipo_cliente', 'creado_manualmente')
        }),
        ('Estadísticas', {
            'fields': ('total_citas', 'total_gastado', 'ultima_visita'),
            'classes': ('collapse',)
        }),
        ('Preferencias de Comunicación', {
            'fields': ('acepta_whatsapp', 'acepta_sms', 'acepta_email', 'acepta_promociones')
        }),
        ('Notas', {
            'fields': ('notas',),
            'classes': ('collapse',)
        }),
        ('Sistema', {
            'fields': ('esta_activo', 'fecha_registro', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Filtrar clientes por negocio del usuario"""
        qs = super().get_queryset(request)
        # Si el usuario tiene un negocio asociado, solo mostrar clientes de ese negocio
        if hasattr(request.user, 'negocio'):
            qs = qs.filter(negocio=request.user.negocio)
        # Si no tiene negocio asociado, es superadmin del sistema y puede ver todos
        return qs

    def get_form(self, request, obj=None, **kwargs):
        """Ocultar campo negocio si el usuario tiene un negocio asociado"""
        form = super().get_form(request, obj, **kwargs)
        # Si el usuario tiene negocio, ocultar el campo de selección
        if hasattr(request.user, 'negocio') and 'negocio' in form.base_fields:
            form.base_fields['negocio'].widget = form.base_fields['negocio'].hidden_widget()
            form.base_fields['negocio'].required = False
        return form

    def save_model(self, request, obj, form, change):
        """Asignar automáticamente el negocio del usuario si no es superadmin"""
        if not change and hasattr(request.user, 'negocio'):
            obj.negocio = request.user.negocio
        super().save_model(request, obj, form, change)

    actions = ['marcar_como_frecuente', 'marcar_como_inactivo']

    def marcar_como_frecuente(self, request, queryset):
        queryset.update(tipo_cliente='frecuente')
        self.message_user(request, f'{queryset.count()} clientes marcados como frecuentes.')
    marcar_como_frecuente.short_description = 'Marcar como clientes frecuentes'

    def marcar_como_inactivo(self, request, queryset):
        queryset.update(tipo_cliente='inactivo')
        self.message_user(request, f'{queryset.count()} clientes marcados como inactivos.')
    marcar_como_inactivo.short_description = 'Marcar como clientes inactivos'
