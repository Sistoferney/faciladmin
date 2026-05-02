from django.contrib import admin
from .models import Servicio


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'negocio', 'precio', 'duracion_minutos', 'frecuencia_dias', 'esta_activo', 'orden')
    list_filter = ('negocio', 'esta_activo', 'requiere_abono')
    search_fields = ('nombre', 'descripcion', 'negocio__nombre')
    list_editable = ('orden', 'esta_activo')

    fieldsets = (
        ('Información Básica', {
            'fields': ('negocio', 'nombre', 'descripcion', 'imagen')
        }),
        ('Precio y Duración', {
            'fields': ('precio', 'duracion_minutos', 'frecuencia_dias')
        }),
        ('Configuración de Abono', {
            'fields': ('requiere_abono', 'monto_abono', 'porcentaje_abono'),
            'classes': ('collapse',)
        }),
        ('Configuración', {
            'fields': ('esta_activo', 'orden')
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Si el usuario no es superadmin, solo mostrar servicios de su negocio
        if not request.user.is_superuser and hasattr(request.user, 'negocio'):
            qs = qs.filter(negocio=request.user.negocio)
        return qs
