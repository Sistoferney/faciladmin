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
        """Filtrar servicios por negocio del usuario"""
        qs = super().get_queryset(request)
        # Si el usuario tiene un negocio asociado, solo mostrar servicios de ese negocio
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
