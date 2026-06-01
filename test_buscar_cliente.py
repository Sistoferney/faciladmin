"""
Script de prueba para verificar la búsqueda de clientes por teléfono
"""
import re

# Simular teléfonos en la BD
telefonos_bd = [
    "+573001111111",  # María González
    "+573002222222",  # Juan Pérez
    "307794370",      # Paola
]

def buscar_por_telefono(telefono_buscado):
    """Busca un teléfono usando la lógica del backend"""
    # Normalizar teléfono buscado
    telefono_digitos = re.sub(r'\D', '', telefono_buscado)

    if len(telefono_digitos) < 10:
        print(f"[X] Telefono muy corto: {telefono_buscado}")
        return None

    # Obtener últimos 10 dígitos
    ultimos_10_buscado = telefono_digitos[-10:]
    print(f"\n[>] Buscando: {telefono_buscado}")
    print(f"   Digitos: {telefono_digitos}")
    print(f"   Ultimos 10: {ultimos_10_buscado}")

    # Buscar en la BD
    for tel_bd in telefonos_bd:
        tel_bd_digitos = re.sub(r'\D', '', tel_bd)

        print(f"   Comparando con {tel_bd} (digitos: {tel_bd_digitos})")

        # 1. Comparar exacto
        if telefono_digitos == tel_bd_digitos:
            print(f"      [OK] ENCONTRADO (comparacion exacta)")
            return tel_bd

        # 2. Comparar últimos 10 dígitos
        ultimos_10_bd = tel_bd_digitos[-10:] if len(tel_bd_digitos) >= 10 else tel_bd_digitos
        if ultimos_10_buscado == ultimos_10_bd:
            print(f"      [OK] ENCONTRADO (ultimos 10 digitos)")
            return tel_bd

        # 3. Comparar últimos 9 dígitos
        ultimos_9_buscado = telefono_digitos[-9:]
        ultimos_9_bd = tel_bd_digitos[-9:] if len(tel_bd_digitos) >= 9 else tel_bd_digitos
        if ultimos_9_buscado == ultimos_9_bd:
            print(f"      [OK] ENCONTRADO (ultimos 9 digitos)")
            return tel_bd

        # 4. Comparar si el buscado termina con el de BD
        if telefono_digitos.endswith(tel_bd_digitos):
            print(f"      [OK] ENCONTRADO (buscado termina con BD)")
            return tel_bd

    print(f"   [X] No encontrado")
    return None

# Pruebas
print("=" * 60)
print("PRUEBAS DE BÚSQUEDA DE TELÉFONO")
print("=" * 60)

# Test 1: Buscar con código de Colombia
buscar_por_telefono("+57 307 794 370")

# Test 2: Buscar sin código (debería buscar con 10 dígitos: 3077943700 o manejar 9)
buscar_por_telefono("3077943700")  # 10 dígitos

# Test 3: Buscar con código de Colombia (debería encontrar a María)
buscar_por_telefono("+57 300 111 1111")

# Test 4: Buscar número que no existe
buscar_por_telefono("+57 300 999 9999")

print("\n" + "=" * 60)
