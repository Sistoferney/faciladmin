# FIX: Configuración de Email en Railway

## Problema Detectado

Los workers de Gunicorn se bloquean al enviar emails porque:

1. **EMAIL_TIMEOUT no estaba configurado** - Django esperaba indefinidamente la respuesta de Gmail
2. **EMAIL_HOST_PASSWORD con espacios** - Las App Passwords de Gmail NO deben tener espacios

## Soluciones Implementadas

### 1. Agregar EMAIL_TIMEOUT (COMPLETADO)
```python
# config/settings/base.py
EMAIL_TIMEOUT = config('EMAIL_TIMEOUT', default=10, cast=int)
```
- Commit: `63228ef`
- Estado: PUSHED a GitHub
- Railway desplegará automáticamente

### 2. Corregir EMAIL_HOST_PASSWORD en Railway

**IMPORTANTE:** La App Password que actualicé podría estar incorrecta.

#### Pasos para obtener la App Password CORRECTA:

1. Ve a tu cuenta de Gmail: seviciofaciladmin@gmail.com
2. Ve a: https://myaccount.google.com/security
3. Busca "Contraseñas de aplicaciones" (App Passwords)
4. Si no la ves, primero activa la verificación en 2 pasos
5. Crea una nueva App Password:
   - Nombre: "FacilAdmin Railway"
   - Copia el código de 16 dígitos (SIN ESPACIOS)
   - Ejemplo: `abcdwxyzabcdwxyz`

#### Actualizar en Railway:

Opción A - Desde el dashboard web:
1. Ve a https://railway.app/
2. Proyecto: faciladmin
3. Servicio: faciladmin
4. Variables
5. Edita `EMAIL_HOST_PASSWORD` y pega la App Password SIN ESPACIOS

Opción B - Desde CLI (reemplaza con tu App Password real):
```bash
railway variables set EMAIL_HOST_PASSWORD="TU_APP_PASSWORD_AQUI" --service faciladmin
```

### 3. Verificar Deployment

Después de actualizar la password, espera 2 minutos y verifica:

```bash
railway logs --service faciladmin
```

Busca:
- ✅ NO debe haber mensajes "CRITICAL WORKER TIMEOUT"
- ✅ Los workers deben arrancar y mantenerse estables
- ✅ Al probar recuperación de contraseña, debe enviarse el email

## Probar el Sistema

1. Ve a: https://faciladmin-production.up.railway.app/login/
2. Haz clic en "Recuperar contraseña"
3. Ingresa un email registrado
4. Verifica que:
   - La página responde inmediatamente (no se congela)
   - Muestra mensaje de éxito
   - El email llega (revisa spam si no aparece)

## Variables de Entorno Correctas

```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seviciofaciladmin@gmail.com
EMAIL_HOST_PASSWORD=<16 caracteres sin espacios>
EMAIL_TIMEOUT=10
```

## Comandos Útiles

Ver variables actuales:
```bash
railway variables --service faciladmin | grep EMAIL
```

Ver logs en tiempo real:
```bash
railway logs --service faciladmin --follow
```

Verificar deployment actual:
```bash
railway status
```

## Diagnóstico de Problemas

### Si siguen apareciendo WORKER TIMEOUT:

1. Verifica que la App Password sea correcta (sin espacios)
2. Verifica que la cuenta de Gmail tenga la verificación en 2 pasos activada
3. Revisa que no haya bloqueos de seguridad en Gmail:
   - Ve a: https://myaccount.google.com/notifications
   - Busca alertas de "Intento de inicio de sesión bloqueado"
   - Autoriza el acceso desde Railway si aparece

### Si los emails no llegan pero no hay timeouts:

- Revisa la carpeta de spam del destinatario
- Verifica los logs: `railway logs --service faciladmin | grep -i "email\|smtp"`
- Confirma que Gmail no esté bloqueando el envío

## Logs Esperados (Correcto)

```
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://0.0.0.0:8080
[INFO] Booting worker with pid: 2
[INFO] Booting worker with pid: 3
```

NO debe aparecer:
```
[CRITICAL] WORKER TIMEOUT (pid:X)  ← MAL
[ERROR] Worker exited with code 1   ← MAL
```

## Estado Actual

- ✅ EMAIL_TIMEOUT agregado
- ⚠️ EMAIL_HOST_PASSWORD actualizada (VERIFICAR QUE SEA CORRECTA)
- ⏳ Deployment en progreso
- ⏳ Pendiente: Probar recuperación de contraseña en producción
