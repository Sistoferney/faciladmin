"""
Script para probar la validación de slugs reservados
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils.text import slugify
from apps.negocios.models import Negocio, SLUGS_RESERVADOS
from apps.authentication.models import Usuario
from django.core.exceptions import ValidationError

print("=== PRUEBA DE SLUGS RESERVADOS ===\n")

# Mostrar palabras reservadas
print(f"Total de palabras reservadas: {len(SLUGS_RESERVADOS)}")
print(f"Palabras reservadas: {', '.join(SLUGS_RESERVADOS[:10])}...\n")

# Obtener o crear un usuario de prueba
try:
    usuario = Usuario.objects.filter(email__contains='test').first()
    if not usuario:
        usuario = Usuario.objects.filter(is_superuser=True).first()

    if not usuario:
        print("No hay usuarios disponibles para la prueba")
        exit()

    print(f"Usuario de prueba: {usuario.email}\n")

    # Probar nombres que deberían ser rechazados
    nombres_prohibidos = ['Admin', 'LOGIN', 'api', 'Dashboard', 'Registro']

    print("=== PROBANDO NOMBRES PROHIBIDOS ===")
    for nombre in nombres_prohibidos:
        slug_generado = slugify(nombre)
        print(f"\nNombre: '{nombre}' -> Slug: '{slug_generado}'")

        try:
            negocio = Negocio(
                administrador=usuario,
                nombre=nombre,
                telefono='1234567890',
            )
            negocio.save()
            print(f"  ERROR: Se permitio crear negocio con slug '{negocio.slug}' (deberia haber sido rechazado)")

            # Limpiar si se creo por error
            negocio.delete()

        except ValidationError as e:
            print(f"  CORRECTO: Rechazado - {e}")
        except Exception as e:
            print(f"  Error inesperado: {e}")

    # Probar que nombres similares SI se aceptan (con sufijo)
    print("\n\n=== PROBANDO NOMBRES SIMILARES (con sufijo automatico) ===")
    nombres_validos_similares = ['Admin Spa', 'Mi Login Salon', 'API Beauty']

    for nombre in nombres_validos_similares:
        slug_generado = slugify(nombre)
        print(f"\nNombre: '{nombre}' -> Slug generado: '{slug_generado}'")

        try:
            # Si el slug base es reservado, el sistema deberia agregar sufijo
            if slug_generado.lower() in SLUGS_RESERVADOS:
                print(f"  Slug base '{slug_generado}' esta reservado, el sistema debe modificarlo...")

        except Exception as e:
            print(f"  Error: {e}")

    # Probar nombres completamente validos
    print("\n\n=== PROBANDO NOMBRES VALIDOS ===")
    nombres_validos = ['Spa Patricia', 'Salon Belleza Maria', 'Barberia El Corte']

    for nombre in nombres_validos:
        slug_generado = slugify(nombre)
        print(f"\nNombre: '{nombre}' -> Slug: '{slug_generado}'")

        if slug_generado.lower() in SLUGS_RESERVADOS:
            print(f"  ADVERTENCIA: Este slug esta reservado!")
        else:
            print(f"  VALIDO: Este slug se puede usar")

except Exception as e:
    print(f"Error general: {e}")
    import traceback
    traceback.print_exc()

print("\n\n=== FIN DE LA PRUEBA ===")
