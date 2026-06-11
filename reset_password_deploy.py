#!/usr/bin/env python
"""
Script temporal para crear/resetear contraseña de admin en producción
Se ejecuta automáticamente en el deploy
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from apps.authentication.models import Usuario

# Crear o resetear contraseña del superadmin
try:
    # Intentar obtener el usuario
    try:
        usuario = Usuario.objects.get(email='sistoferney@gmail.com')
        usuario.set_password('Admin2024Seguro!')
        usuario.save()
        print('✓ Contraseña de admin reseteada exitosamente')
    except Usuario.DoesNotExist:
        # Si no existe, crearlo
        usuario = Usuario.objects.create_superuser(
            email='sistoferney@gmail.com',
            nombre='Administrador',
            password='Admin2024Seguro!'
        )
        print('✓ Superusuario creado exitosamente')

    print('✓ Email: sistoferney@gmail.com')
    print('✓ Password: Admin2024Seguro!')
    print('✓ Puedes iniciar sesion en /admin/')
except Exception as e:
    print(f'Error al crear/resetear contraseña: {e}')
    import traceback
    traceback.print_exc()
