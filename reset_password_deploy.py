#!/usr/bin/env python
"""
Script temporal para resetear contraseña de admin en producción
Se ejecuta automáticamente en el deploy
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from apps.authentication.models import Usuario

# Resetear contraseña del superadmin
try:
    usuario = Usuario.objects.get(email='sistoferney@gmail.com')
    usuario.set_password('Admin2024Seguro!')
    usuario.save()
    print('✓ Contraseña de admin reseteada exitosamente')
    print('✓ Email: sistoferney@gmail.com')
    print('✓ Password: Admin2024Seguro!')
except Exception as e:
    print(f'Error al resetear contraseña: {e}')
