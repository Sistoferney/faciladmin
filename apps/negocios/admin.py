from django.contrib import admin
from .models import Negocio, ConfiguracionHorario, BloqueoAgenda


class ConfiguracionHorarioInline(admin.TabularInline):
    model = ConfiguracionHorario
    extra = 7
    max_num = 7


@admin.register(Negocio)
class NegocioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'administrador', 'telefono', 'esta_activo', 'acepta_reservas_online')
    list_filter = ('tipo', 'esta_activo', 'acepta_reservas_online', 'fecha_creacion')
    search_fields = ('nombre', 'administrador__email', 'telefono', 'ciudad')
    prepopulated_fields = {'slug': ('nombre',)}
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'url_publica')

    fieldsets = (
        ('Información Básica', {
            'fields': ('administrador', 'nombre', 'tipo', 'descripcion', 'slug')
        }),
        ('Contacto', {
            'fields': ('telefono', 'email', 'whatsapp')
        }),
        ('Ubicación', {
            'fields': ('direccion', 'ciudad', 'estado', 'codigo_postal')
        }),
        ('Horarios', {
            'fields': ('horario_apertura', 'horario_cierre', 'dias_atencion')
        }),
        ('Configuración de Abonos', {
            'fields': ('requiere_abono', 'porcentaje_abono', 'monto_abono_fijo',
                      'banco', 'numero_cuenta', 'clabe', 'titular_cuenta')
        }),
        ('Personalización', {
            'fields': ('logo', 'imagen_portada', 'color_primario', 'color_secundario')
        }),
        ('Redes Sociales', {
            'fields': ('facebook', 'instagram', 'twitter'),
            'classes': ('collapse',)
        }),
        ('Configuración', {
            'fields': ('esta_activo', 'acepta_reservas_online')
        }),
        ('Información del Sistema', {
            'fields': ('url_publica', 'fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

    inlines = [ConfiguracionHorarioInline]

    def get_queryset(self, request):
        """Filtrar negocios: cada admin solo ve su propio negocio"""
        qs = super().get_queryset(request)
        # Si el usuario tiene un negocio asociado, solo mostrar ese negocio
        if hasattr(request.user, 'negocio'):
            qs = qs.filter(id=request.user.negocio.id)
        # Si no tiene negocio asociado, es superadmin del sistema y puede ver todos
        return qs

    def has_add_permission(self, request):
        """Los admins de negocio no pueden crear nuevos negocios desde el admin"""
        # Solo el superadmin del sistema puede crear negocios
        # Los negocios se crean desde la página de registro
        if hasattr(request.user, 'negocio'):
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        """Los admins de negocio no pueden eliminar su negocio"""
        if hasattr(request.user, 'negocio'):
            return False
        return super().has_delete_permission(request, obj)


@admin.register(BloqueoAgenda)
class BloqueoAgendaAdmin(admin.ModelAdmin):
    list_display = ('negocio', 'fecha_inicio', 'fecha_fin', 'motivo_interno', 'esta_activo')
    list_filter = ('esta_activo', 'fecha_inicio', 'negocio')
    search_fields = ('negocio__nombre', 'motivo_interno')
    date_hierarchy = 'fecha_inicio'

    fieldsets = (
        (None, {
            'fields': ('negocio', 'fecha_inicio', 'fecha_fin', 'motivo_interno', 'esta_activo')
        }),
    )

    def get_queryset(self, request):
        """Filtrar bloqueos por negocio del usuario"""
        qs = super().get_queryset(request)
        if hasattr(request.user, 'negocio'):
            qs = qs.filter(negocio=request.user.negocio)
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
