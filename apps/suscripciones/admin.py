from django.contrib import admin
from django.utils.html import format_html
from .models import (
    PlanSuscripcion,
    Suscripcion,
    PagoSuscripcion,
    Cupon,
    UsoCupon,
    RegistroNegocio,
    ProgramaReferidos
)


@admin.register(PlanSuscripcion)
class PlanSuscripcionAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'precio_formatted', 'duracion_dias', 'activo']
    list_filter = ['tipo', 'activo']
    search_fields = ['nombre', 'descripcion']

    fieldsets = [
        ('Información Básica', {
            'fields': ['nombre', 'tipo', 'precio', 'duracion_dias', 'descripcion', 'activo']
        }),
        ('Límites del Plan', {
            'fields': ['max_citas_mes', 'max_servicios', 'max_clientes', 'push_notifications', 'soporte_prioritario'],
            'description': 'Dejar en blanco para ilimitado'
        })
    ]

    def precio_formatted(self, obj):
        return f"${obj.precio:,.0f}"
    precio_formatted.short_description = 'Precio'


@admin.register(Suscripcion)
class SuscripcionAdmin(admin.ModelAdmin):
    list_display = ['negocio', 'plan', 'estado_badge', 'fecha_inicio', 'fecha_fin', 'dias_restantes']
    list_filter = ['estado', 'plan', 'auto_renovacion']
    search_fields = ['negocio__nombre', 'negocio__email']
    readonly_fields = ['creado_en', 'actualizado_en', 'dias_restantes']

    fieldsets = [
        ('Información del Negocio', {
            'fields': ['negocio', 'plan', 'estado']
        }),
        ('Fechas', {
            'fields': ['fecha_inicio', 'fecha_fin', 'fecha_cancelacion']
        }),
        ('Configuración de Pago', {
            'fields': ['metodo_pago', 'token_pago', 'referencia_externa', 'auto_renovacion']
        }),
        ('Auditoría', {
            'fields': ['creado_en', 'actualizado_en'],
            'classes': ['collapse']
        })
    ]

    def estado_badge(self, obj):
        colors = {
            'trial': '#17a2b8',
            'activa': '#28a745',
            'vencida': '#dc3545',
            'cancelada': '#6c757d',
            'suspendida': '#ffc107'
        }
        color = colors.get(obj.estado, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'


@admin.register(PagoSuscripcion)
class PagoSuscripcionAdmin(admin.ModelAdmin):
    list_display = ['suscripcion', 'monto_formatted', 'estado_badge', 'pasarela', 'metodo_pago', 'fecha_pago']
    list_filter = ['estado', 'pasarela', 'metodo_pago']
    search_fields = ['suscripcion__negocio__nombre', 'transaccion_id', 'referencia']
    readonly_fields = ['creado_en', 'metadata']

    fieldsets = [
        ('Información del Pago', {
            'fields': ['suscripcion', 'monto', 'estado', 'fecha_pago']
        }),
        ('Pasarela de Pago', {
            'fields': ['pasarela', 'metodo_pago', 'transaccion_id', 'referencia']
        }),
        ('Metadata', {
            'fields': ['metadata'],
            'classes': ['collapse']
        }),
        ('Auditoría', {
            'fields': ['creado_en'],
            'classes': ['collapse']
        })
    ]

    def monto_formatted(self, obj):
        return f"${obj.monto:,.0f}"
    monto_formatted.short_description = 'Monto'

    def estado_badge(self, obj):
        colors = {
            'pendiente': '#ffc107',
            'aprobado': '#28a745',
            'rechazado': '#dc3545',
            'reembolsado': '#6c757d'
        }
        color = colors.get(obj.estado, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'


@admin.register(Cupon)
class CuponAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'negocio_asignado', 'usado_badge', 'valido_badge', 'fecha_uso', 'creado_en']
    list_filter = ['activo', 'usado']
    search_fields = ['codigo', 'descripcion', 'negocio_asignado__nombre']
    readonly_fields = ['usado', 'fecha_uso', 'creado_en']
    raw_id_fields = ['negocio_asignado', 'creado_por']

    fieldsets = [
        ('Información del Cupón', {
            'fields': ['codigo', 'descripcion', 'activo']
        }),
        ('Asignación', {
            'fields': ['negocio_asignado'],
            'description': 'Si se asigna a un negocio específico, solo ese negocio podrá canjearlo. Dejar vacío para uso general.'
        }),
        ('Vigencia', {
            'fields': ['fecha_inicio', 'fecha_expiracion']
        }),
        ('Estado de Uso', {
            'fields': ['usado', 'fecha_uso'],
            'classes': ['collapse']
        }),
        ('Auditoría', {
            'fields': ['creado_por', 'creado_en'],
            'classes': ['collapse']
        })
    ]

    def usado_badge(self, obj):
        if obj.usado:
            return format_html('<span style="color: orange;">✓ Canjeado</span>')
        return format_html('<span style="color: blue;">○ Disponible</span>')
    usado_badge.short_description = 'Estado'

    def valido_badge(self, obj):
        if obj.esta_valido:
            return format_html('<span style="color: green;">✓ Válido</span>')
        return format_html('<span style="color: red;">✗ Expirado/Usado</span>')
    valido_badge.short_description = 'Validez'


@admin.register(UsoCupon)
class UsoCuponAdmin(admin.ModelAdmin):
    list_display = ['cupon', 'negocio', 'meses_extendidos', 'aplicado_en']
    list_filter = ['aplicado_en']
    search_fields = ['cupon__codigo', 'negocio__nombre']
    readonly_fields = ['aplicado_en', 'meses_extendidos']

    def has_add_permission(self, request):
        # Solo se crean usos cuando se canjea un cupón
        return False


@admin.register(RegistroNegocio)
class RegistroNegocioAdmin(admin.ModelAdmin):
    list_display = ['nombre_completo', 'email', 'telefono', 'estado_badge', 'creado_en']
    list_filter = ['estado', 'creado_en']
    search_fields = ['nombre', 'apellido', 'email', 'telefono']
    readonly_fields = ['token_validacion', 'fecha_token_expira', 'email_validado_en', 'creado_en', 'actualizado_en']

    fieldsets = [
        ('Datos del Usuario', {
            'fields': ['nombre', 'apellido', 'email', 'telefono']
        }),
        ('Validación', {
            'fields': ['estado', 'token_validacion', 'fecha_token_expira', 'email_validado_en']
        }),
        ('Negocio Creado', {
            'fields': ['negocio_creado']
        }),
        ('Auditoría', {
            'fields': ['creado_en', 'actualizado_en'],
            'classes': ['collapse']
        })
    ]

    def nombre_completo(self, obj):
        return f"{obj.nombre} {obj.apellido}"
    nombre_completo.short_description = 'Nombre'

    def estado_badge(self, obj):
        colors = {
            'pendiente_email': '#ffc107',
            'completado': '#28a745',
            'expirado': '#dc3545'
        }
        color = colors.get(obj.estado, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'


@admin.register(ProgramaReferidos)
class ProgramaReferidosAdmin(admin.ModelAdmin):
    list_display = ['negocio', 'referidos_display', 'estado_badge', 'total_cupones_generados', 'ultimo_cupon_display']
    list_filter = ['activo', 'creado_en']
    search_fields = ['negocio__nombre']
    readonly_fields = ['activo', 'total_cupones_generados', 'fecha_ultimo_cupon', 'creado_en', 'actualizado_en']
    raw_id_fields = ['negocio', 'negocio_referido_1', 'negocio_referido_2', 'negocio_referido_3']

    fieldsets = [
        ('Negocio Principal', {
            'fields': ['negocio']
        }),
        ('Negocios Referidos', {
            'fields': ['negocio_referido_1', 'negocio_referido_2', 'negocio_referido_3'],
            'description': 'Los 3 negocios que fueron referidos. Deben estar activos para generar cupones.'
        }),
        ('Estado del Programa', {
            'fields': ['activo', 'total_cupones_generados', 'fecha_ultimo_cupon']
        }),
        ('Auditoría', {
            'fields': ['creado_en', 'actualizado_en'],
            'classes': ['collapse']
        })
    ]

    def referidos_display(self, obj):
        count = obj.referidos_activos()
        if count == 3:
            color = 'green'
            icon = '✓'
        elif count > 0:
            color = 'orange'
            icon = '○'
        else:
            color = 'red'
            icon = '✗'
        return format_html(
            '<span style="color: {};">{} {}/3</span>',
            color, icon, count
        )
    referidos_display.short_description = 'Referidos Activos'

    def estado_badge(self, obj):
        if obj.activo:
            return format_html('<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">✓ Activo</span>')
        return format_html('<span style="background-color: #6c757d; color: white; padding: 3px 10px; border-radius: 3px;">○ Inactivo</span>')
    estado_badge.short_description = 'Estado'

    def ultimo_cupon_display(self, obj):
        if obj.fecha_ultimo_cupon:
            return obj.fecha_ultimo_cupon.strftime('%d/%m/%Y')
        return '-'
    ultimo_cupon_display.short_description = 'Último Cupón'

    actions = ['actualizar_estados', 'generar_cupones']

    def actualizar_estados(self, request, queryset):
        """Actualiza el estado de los programas seleccionados"""
        actualizados = 0
        for programa in queryset:
            programa.actualizar_estado()
            actualizados += 1
        self.message_user(request, f'{actualizados} programa(s) actualizado(s)')
    actualizar_estados.short_description = 'Actualizar estado de referidos'

    def generar_cupones(self, request, queryset):
        """Genera cupones para los programas que cumplen requisitos"""
        generados = 0
        errores = []
        for programa in queryset:
            exito, mensaje, cupon = programa.generar_cupon_mensual()
            if exito:
                generados += 1
            else:
                errores.append(f"{programa.negocio.nombre}: {mensaje}")

        if generados > 0:
            self.message_user(request, f'{generados} cupón(es) generado(s) exitosamente')
        if errores:
            self.message_user(request, f'Errores: {", ".join(errores[:5])}', level='warning')
    generar_cupones.short_description = 'Generar cupones mensuales'
