#!/usr/bin/env python
"""
Script para limpiar usuarios incompletos (sin negocio asociado)
Ejecutar: railway run python limpiar_usuario_incompleto.py

IMPORTANTE: Este script elimina usuarios que no tienen un negocio asociado.
Solo úsalo para limpiar registros incompletos de intentos fallidos.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from apps.authentication.models import Usuario
from apps.suscripciones.models import RegistroNegocio

print("=" * 70)
print("LIMPIEZA DE USUARIOS INCOMPLETOS")
print("=" * 70)

# Buscar usuarios sin negocio asociado
usuarios_sin_negocio = []
for user in Usuario.objects.all():
    # Verificar si tiene algún negocio asociado
    if not user.negocios.exists():
        usuarios_sin_negocio.append(user)

if not usuarios_sin_negocio:
    print("\n✓ No se encontraron usuarios incompletos.")
    print("  Todos los usuarios tienen un negocio asociado.")
else:
    print(f"\n⚠ Se encontraron {len(usuarios_sin_negocio)} usuario(s) sin negocio asociado:")
    print("-" * 70)

    for user in usuarios_sin_negocio:
        print(f"\n📧 Email: {user.email}")
        print(f"   Nombre: {user.nombre}")
        print(f"   Teléfono: {user.telefono}")
        print(f"   Creado: {user.created_at}")

        # Verificar si tiene un RegistroNegocio asociado
        try:
            registro = RegistroNegocio.objects.get(email=user.email)
            print(f"   Estado registro: {registro.get_estado_display()}")
            print(f"   Token válido: {'Sí' if registro.token_valido else 'No'}")
        except RegistroNegocio.DoesNotExist:
            print(f"   ⚠ No tiene registro asociado")

    print("\n" + "=" * 70)
    respuesta = input("\n¿Deseas eliminar estos usuarios incompletos? (sí/no): ").strip().lower()

    if respuesta in ['sí', 'si', 's', 'yes', 'y']:
        count = 0
        for user in usuarios_sin_negocio:
            email = user.email
            user.delete()
            count += 1
            print(f"✓ Usuario eliminado: {email}")

        print(f"\n✓ Se eliminaron {count} usuario(s) incompleto(s)")
        print("\nAhora los usuarios pueden completar su registro usando el enlace del email.")
    else:
        print("\nOperación cancelada. No se eliminaron usuarios.")

print("\n" + "=" * 70)
print("FIN DE LA LIMPIEZA")
print("=" * 70)
