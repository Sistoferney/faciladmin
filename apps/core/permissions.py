"""
Utilidades para gestión de permisos de usuarios
"""
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


def asignar_permisos_admin_negocio(usuario):
    """
    Asigna los permisos necesarios a un administrador de negocio

    Args:
        usuario: Instancia del modelo Usuario
    """
    # Lista de permisos a asignar
    # Formato: (app_label, model_name, [permissions])
    permisos_config = [
        # Negocios - solo puede ver y editar su propio negocio
        ('negocios', 'negocio', ['view', 'change']),
        ('negocios', 'configuracionhorario', ['add', 'view', 'change', 'delete']),
        ('negocios', 'bloqueoagenda', ['add', 'view', 'change', 'delete']),

        # Servicios - control total
        ('servicios', 'servicio', ['add', 'view', 'change', 'delete']),

        # Clientes - control total
        ('clientes', 'cliente', ['add', 'view', 'change', 'delete']),

        # Citas - control total
        ('citas', 'cita', ['add', 'view', 'change', 'delete']),

        # Abonos - control total
        ('abonos', 'abono', ['add', 'view', 'change', 'delete']),

        # Notificaciones - solo ver y cambiar (se crean automáticamente)
        ('notificaciones', 'notificacion', ['view', 'change']),

        # Promociones - control total
        ('promociones', 'promocion', ['add', 'view', 'change', 'delete']),
    ]

    permisos_a_asignar = []

    for app_label, model_name, perms in permisos_config:
        try:
            content_type = ContentType.objects.get(app_label=app_label, model=model_name)

            for perm_codename in perms:
                # El codename tiene el formato: add_modelname, change_modelname, etc.
                codename = f"{perm_codename}_{model_name}"

                try:
                    permission = Permission.objects.get(
                        codename=codename,
                        content_type=content_type
                    )
                    permisos_a_asignar.append(permission)
                except Permission.DoesNotExist:
                    print(f"⚠ Permiso no encontrado: {codename} para {app_label}.{model_name}")

        except ContentType.DoesNotExist:
            print(f"⚠ ContentType no encontrado: {app_label}.{model_name}")

    # Asignar todos los permisos al usuario
    usuario.user_permissions.set(permisos_a_asignar)
    usuario.save()

    return len(permisos_a_asignar)
