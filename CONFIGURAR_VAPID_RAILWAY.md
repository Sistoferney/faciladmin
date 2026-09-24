# Configurar VAPID Keys en Railway

## El Problema
Las VAPID keys actuales en Railway están corruptas, causando el error:
```
Could not deserialize key data... ASN.1 parsing error: invalid length
```

## La Solución
Reemplazar las VAPID keys con nuevas keys correctamente formateadas.

---

## PASO 1: Generar Nuevas VAPID Keys

Ejecuta este comando en tu terminal local:

```bash
python -c "
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import base64

private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
public_key = private_key.public_key()

private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
).decode('utf-8')

public_numbers = public_key.public_numbers()
x = public_numbers.x.to_bytes(32, byteorder='big')
y = public_numbers.y.to_bytes(32, byteorder='big')
public_key_bytes = b'\x04' + x + y
public_b64 = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')

private_oneline = private_pem.replace('\n', '\\\\n')

print('VAPID_PUBLIC_KEY:')
print(public_b64)
print()
print('VAPID_PRIVATE_KEY:')
print(private_oneline)
"
```

---

## PASO 2: Configurar en Railway

1. Ve a tu proyecto Railway: https://railway.app
2. Selecciona el servicio "faciladmin"
3. Ve a la pestaña **"Variables"**
4. Actualiza/Agrega estas variables:

### Variable 1: `VAPID_PUBLIC_KEY`
**Valor:** (copia el valor que generaste arriba, sin BEGIN/END)
```
Ejemplo: BC29nNyd7jrXnKlaAp3briq2t3ihjGwOuGf48gLsmnY7Tiayv_D239f5eNWNgYmh8EHF056x3Snu6bQfzTLh6wA
```

### Variable 2: `VAPID_PRIVATE_KEY`
**Valor:** (copia TODO el texto con \\n, incluyendo -----BEGIN PRIVATE KEY----- y -----END PRIVATE KEY-----)
```
Ejemplo: -----BEGIN PRIVATE KEY-----\nMIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQg...\n-----END PRIVATE KEY-----\n
```

**IMPORTANTE:** El valor debe tener `\\n` (barra invertida + n) en lugar de saltos de línea reales.

### Variable 3: `VAPID_ADMIN_EMAIL`
**Valor:**
```
admin@faciladmin.com
```

---

## PASO 3: Guardar y Redesplegar

1. Haz clic en **"Save"** o **"Update"**
2. Railway automáticamente redesplegar la aplicación
3. Espera 1-2 minutos

---

## PASO 4: Verificar

1. Crea una nueva cita desde la mini-página
2. Deberías recibir la notificación push en tu dispositivo

---

## Notas

- Las nuevas VAPID keys son diferentes a las anteriores
- Esto significa que **todas las suscripciones existentes quedarán inválidas**
- Los usuarios deberán **volver a suscribirse** (desinstalar y reinstalar la PWA, o activar notificaciones nuevamente)
- Esto es normal y necesario cuando cambias las VAPID keys

---

## Troubleshooting

Si sigue sin funcionar:

1. Verifica que las variables estén exactamente como se indica (con `\\n`, no saltos de línea reales)
2. Verifica que no haya espacios extra al inicio o final
3. Revisa los logs de Railway para ver si hay errores diferentes
