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
