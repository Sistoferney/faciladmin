from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    """Admin personalizado para el modelo Usuario"""

    list_display = ('email', 'nombre', 'telefono', 'is_staff', 'esta_activo', 'fecha_registro')
    list_filter = ('is_staff', 'is_superuser', 'esta_activo', 'fecha_registro')
    search_fields = ('email', 'nombre', 'telefono')
    ordering = ('-fecha_registro',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {'fields': ('nombre', 'telefono')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nombre', 'telefono', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )

    filter_horizontal = ('groups', 'user_permissions',)
