#!/usr/bin/env python
"""
Script para limpiar el usuario específico sistofguarin@gmail.com
Ejecutar: railway run python fix_email_sistof.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from apps.authentication.models import Usuario
from apps.suscripciones.models import RegistroNegocio

EMAIL = 'sistofguarin@gmail.com'

print("=" * 70)
print(f"LIMPIEZA DE USUARIO: {EMAIL}")
print("=" * 70)

# Verificar si existe el usuario
try:
    user = Usuario.objects.get(email=EMAIL)
    print(f"\n✓ Usuario encontrado:")
    print(f"   Email: {user.email}")
    print(f"   Nombre: {user.nombre}")
    print(f"   Teléfono: {user.telefono}")
    print(f"   Creado: {user.created_at}")

    # Verificar si tiene negocio
    if user.negocios.exists():
        print(f"\n⚠ ATENCIÓN: Este usuario tiene {user.negocios.count()} negocio(s) asociado(s):")
        for negocio in user.negocios.all():
            print(f"   - {negocio.nombre}")
        print("\n❌ NO SE PUEDE ELIMINAR. El usuario tiene datos importantes.")
    else:
        print(f"\n✓ El usuario NO tiene negocios asociados (es seguro eliminarlo)")

        # Verificar registro
        try:
            registro = RegistroNegocio.objects.get(email=EMAIL)
            print(f"\n✓ RegistroNegocio encontrado:")
            print(f"   Estado: {registro.get_estado_display()}")
            print(f"   Token válido: {'Sí' if registro.token_valido else 'No'}")
        except RegistroNegocio.DoesNotExist:
            print(f"\n⚠ No hay RegistroNegocio asociado")

        # Confirmar eliminación
        print("\n" + "=" * 70)
        print("Se eliminará el usuario incompleto para que puedas registrarte de nuevo.")
        print("=" * 70)

        user.delete()
        print(f"\n✓ Usuario {EMAIL} eliminado exitosamente")
        print("\nAhora puedes usar el enlace del email para completar tu registro.")

except Usuario.DoesNotExist:
    print(f"\n✓ El usuario {EMAIL} NO existe en la base de datos.")
    print("   Puedes completar el registro sin problemas.")

print("\n" + "=" * 70)
print("FIN")
print("=" * 70)
