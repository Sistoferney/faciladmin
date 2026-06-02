from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm
from .models import Usuario


class UsuarioChangeForm(UserChangeForm):
    """Formulario personalizado para cambio de usuario"""
    class Meta(UserChangeForm.Meta):
        model = Usuario
        fields = '__all__'


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    """Admin personalizado para el modelo Usuario"""

    form = UsuarioChangeForm

    # Configurar el campo de usuario (email en lugar de username)
    ordering = ('email',)
    list_display = ('email', 'nombre', 'telefono', 'is_staff', 'esta_activo', 'fecha_registro')
    list_filter = ('is_staff', 'is_superuser', 'esta_activo', 'fecha_registro')
    search_fields = ('email', 'nombre', 'telefono')

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
