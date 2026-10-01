#!/usr/bin/env python
"""
Script para encontrar y corregir teléfonos duplicados en Usuario
DEBE ejecutarse ANTES de aplicar la migración que hace telefono unique

Ejecutar: railway run python fix_telefonos_duplicados.py
"""
import os
import django
from collections import defaultdict

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from apps.authentication.models import Usuario

print("=" * 70)
print("BÚSQUEDA DE TELÉFONOS DUPLICADOS")
print("=" * 70)

# Buscar duplicados
telefonos_count = defaultdict(list)
for user in Usuario.objects.all():
    if user.telefono:  # Solo contar si tiene teléfono
        telefonos_count[user.telefono].append(user)

# Filtrar solo los duplicados
duplicados = {tel: users for tel, users in telefonos_count.items() if len(users) > 1}

if not duplicados:
    print("\n✓ No se encontraron teléfonos duplicados.")
    print("  Puedes aplicar las migraciones sin problemas.")
else:
    print(f"\n⚠ Se encontraron {len(duplicados)} teléfono(s) duplicado(s):")
    print("=" * 70)

    for telefono, usuarios in duplicados.items():
        print(f"\n📱 Teléfono: {telefono} ({len(usuarios)} usuarios)")
        print("-" * 70)
        for idx, user in enumerate(usuarios, 1):
            print(f"  {idx}. ID: {user.id} | Email: {user.email} | Nombre: {user.nombre}")
            try:
                # Verificar si tiene negocio asociado (relación desde Negocio)
                negocios = user.negocio_set.all() if hasattr(user, 'negocio_set') else []
                if negocios:
                    for negocio in negocios:
                        print(f"     - Negocio: {negocio.nombre}")
                else:
                    print(f"     - Sin negocio asociado")
            except:
                print(f"     - Sin negocio asociado")

    print("\n" + "=" * 70)
    print("OPCIONES PARA CORREGIR:")
    print("=" * 70)
    print("1. Eliminar usuarios SIN negocio (más seguro)")
    print("2. Agregar sufijo -1, -2, etc. a teléfonos duplicados")
    print("3. Corregir manualmente")
    print("0. Salir sin hacer cambios")

    opcion = input("\nSelecciona una opción (0-3): ").strip()

    if opcion == "1":
        # Eliminar usuarios sin negocio
        print("\n⚙️ Eliminando usuarios sin negocio asociado...")
        count_eliminados = 0

        for telefono, usuarios in duplicados.items():
            # Mantener solo usuarios CON negocio
            def tiene_negocio(user):
                try:
                    return hasattr(user, 'negocio_set') and user.negocio_set.exists()
                except:
                    return False

            usuarios_con_negocio = [u for u in usuarios if tiene_negocio(u)]
            usuarios_sin_negocio = [u for u in usuarios if not tiene_negocio(u)]

            if usuarios_con_negocio and usuarios_sin_negocio:
                for user in usuarios_sin_negocio:
                    print(f"  ✓ Eliminando: {user.email} (sin negocio)")
                    user.delete()
                    count_eliminados += 1
            elif len(usuarios_sin_negocio) == len(usuarios):
                # Todos sin negocio - mantener el más reciente
                usuarios_ordenados = sorted(usuarios, key=lambda u: u.fecha_registro, reverse=True)
                print(f"  ⚠ Todos sin negocio. Manteniendo más reciente: {usuarios_ordenados[0].email}")
                for user in usuarios_ordenados[1:]:
                    print(f"  ✓ Eliminando: {user.email}")
                    user.delete()
                    count_eliminados += 1

        print(f"\n✓ Se eliminaron {count_eliminados} usuario(s)")

    elif opcion == "2":
        # Agregar sufijos
        print("\n⚙️ Agregando sufijos a teléfonos duplicados...")
        count_actualizados = 0

        for telefono, usuarios in duplicados.items():
            # Ordenar por fecha de registro (el más antiguo mantiene el original)
            usuarios_ordenados = sorted(usuarios, key=lambda u: u.fecha_registro)

            # El primero mantiene el teléfono original
            print(f"\n  Teléfono {telefono}:")
            print(f"    ✓ {usuarios_ordenados[0].email} mantiene {telefono}")

            # Los demás reciben sufijo
            for idx, user in enumerate(usuarios_ordenados[1:], 1):
                nuevo_telefono = f"{telefono}-{idx}"
                print(f"    → {user.email}: {telefono} → {nuevo_telefono}")
                user.telefono = nuevo_telefono
                user.save()
                count_actualizados += 1

        print(f"\n✓ Se actualizaron {count_actualizados} teléfono(s)")

    elif opcion == "3":
        print("\n📝 Corrección manual:")
        print("   1. Conéctate a la base de datos")
        print("   2. Actualiza los teléfonos manualmente")
        print("   3. Vuelve a ejecutar este script para verificar")

    else:
        print("\n❌ Operación cancelada")

print("\n" + "=" * 70)
print("FIN")
print("=" * 70)
