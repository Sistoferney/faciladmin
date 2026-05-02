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
        qs = super().get_queryset(request)
        # Si el usuario no es superadmin, solo mostrar clientes de su negocio
        if not request.user.is_superuser and hasattr(request.user, 'negocio'):
            qs = qs.filter(negocio=request.user.negocio)
        return qs

    actions = ['marcar_como_frecuente', 'marcar_como_inactivo']

    def marcar_como_frecuente(self, request, queryset):
        queryset.update(tipo_cliente='frecuente')
        self.message_user(request, f'{queryset.count()} clientes marcados como frecuentes.')
    marcar_como_frecuente.short_description = 'Marcar como clientes frecuentes'

    def marcar_como_inactivo(self, request, queryset):
        queryset.update(tipo_cliente='inactivo')
        self.message_user(request, f'{queryset.count()} clientes marcados como inactivos.')
    marcar_como_inactivo.short_description = 'Marcar como clientes inactivos'
