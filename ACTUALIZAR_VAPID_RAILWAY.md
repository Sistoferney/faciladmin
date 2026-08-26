# Actualizar Claves VAPID en Railway

## Problema Solucionado

Se corrigió el error: **"Failed to execute 'atob' on 'Window': The string to be decoded is not correctly encoded"**

### Causa del Error
Las claves VAPID anteriores estaban en formato DER/ASN.1 (con headers de certificado), pero Web Push requiere claves en formato **raw URL-safe base64**.

### Solución
Se generaron nuevas claves VAPID en el formato correcto usando el script `generar_vapid_keys.py`.

---

## Instrucciones para Actualizar en Railway

### 1. Acceder al Proyecto en Railway
1. Ve a [railway.app](https://railway.app)
2. Selecciona tu proyecto `faciladmin`
3. Ve a la pestaña **Variables**

### 2. Actualizar las Variables de Entorno

Reemplaza las variables VAPID con estos nuevos valores:

#### VAPID_PUBLIC_KEY
```
BFTdSJKB_JA87CV92o2lUWqrr0Wuk_67ibyYDBzg0p8YbZRlf5CSVLUraDsMkFBYZI8LIHQ_xYZflyj29zlO7hU
```

#### VAPID_PRIVATE_KEY
```
-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgmVttERBbcxGl5/XU
/jNetvt3+VPupv6ImBw37+Nvn/qhRANCAARU3UiSgfyQPOwlfdqNpVFqq69FrpP+
u4m8mAwc4NKfGG2UZX+QklS1K2g7DJBQWGSPCyB0P8WGX5co9vc5Tu4V
-----END PRIVATE KEY-----
```

**IMPORTANTE:** En Railway, pega la clave privada en una sola línea con `\n` para los saltos de línea:
```
-----BEGIN PRIVATE KEY-----\nMIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgmVttERBbcxGl5/XU\n/jNetvt3+VPupv6ImBw37+Nvn/qhRANCAARU3UiSgfyQPOwlfdqNpVFqq69FrpP+\nu4m8mAwc4NKfGG2UZX+QklS1K2g7DJBQWGSPCyB0P8WGX5co9vc5Tu4V\n-----END PRIVATE KEY-----
```

#### VAPID_ADMIN_EMAIL
```
admin@faciladmin.com
```

### 3. Guardar y Redesplegar
1. Haz clic en **Save** después de actualizar cada variable
2. Railway redesplegará automáticamente la aplicación
3. Espera a que el deployment termine (icono verde de "Success")

### 4. Verificar en Producción

Después del redespliegue:

1. Ve a `https://faciladmin.app/admin/` (o tu dominio)
2. Inicia sesión
3. Haz clic en el banner "Activar Notificaciones"
4. Acepta los permisos
5. **Debería funcionar sin errores**

---

## ¿Por qué cambiar las claves?

### Formato Anterior (INCORRECTO para Web Push)
```
VAPID_PUBLIC_KEY=BFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAED7PqJqYnQlKOwq+pQTeFnGa2NB/ElK/d...
```
- Incluye header DER/ASN.1: `BFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE`
- Formato de certificado completo
- No compatible con `atob()` en navegador

### Formato Nuevo (CORRECTO para Web Push)
```
VAPID_PUBLIC_KEY=BFTdSJKB_JA87CV92o2lUWqrr0Wuk_67ibyYDBzg0p8YbZRlf5CSVLUraDsMkFBYZI8LIHQ_xYZflyj29zlO7hU
```
- Solo los 65 bytes de la clave pública EC
- Formato raw URL-safe base64
- Compatible con Web Push API

---

## Notas Importantes

⚠️ **Las suscripciones antiguas dejarán de funcionar**
- Los usuarios que ya activaron notificaciones necesitarán **reactivarlas**
- Esto es porque las claves VAPID cambiaron
- Es un cambio único necesario para corregir el error

✅ **Después de actualizar:**
- El error "atob" desaparecerá
- Las notificaciones funcionarán en Android, iOS y Windows
- No habrá más problemas de encoding

---

## Regenerar Claves (Si es necesario)

Si en el futuro necesitas generar nuevas claves VAPID:

```bash
python generar_vapid_keys.py
```

Esto creará un nuevo par de claves en el formato correcto.
