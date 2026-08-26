"""
Script para generar claves VAPID correctamente para Web Push
"""
from py_vapid import Vapid
from cryptography.hazmat.primitives import serialization
import base64

# Generar nuevas claves VAPID
vapid = Vapid()
vapid.generate_keys()

# Obtener las claves
private_key_pem = vapid.private_pem().decode('utf-8')

# Obtener clave pública en formato URL-safe base64
# El método save_public_key() guarda en formato URL-safe
public_key_urlsafe = vapid.public_key.public_bytes(
    encoding=serialization.Encoding.X962,
    format=serialization.PublicFormat.UncompressedPoint
)

# Convertir a base64 URL-safe
public_key_base64 = base64.urlsafe_b64encode(public_key_urlsafe).decode('utf-8').rstrip('=')

print("=" * 70)
print("CLAVES VAPID GENERADAS CORRECTAMENTE")
print("=" * 70)
print("\nCopia estas claves en tu archivo .env:\n")
print(f"VAPID_PUBLIC_KEY={public_key_base64}")
print(f"\nVAPID_PRIVATE_KEY={private_key_pem.strip()}")
print("\nVAPID_ADMIN_EMAIL=admin@faciladmin.com")
print("=" * 70)
