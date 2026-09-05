# Diagnóstico: Notificaciones Push No Llegan a Usuarios PWA

## Resumen de la Investigación

Se ha completado la revisión del sistema de notificaciones push y se ha implementado el Badge API. La infraestructura PWA está correctamente configurada, pero las notificaciones pueden no estar llegando debido a varios factores.

## Estado Actual del Sistema

### ✅ Componentes Verificados como CORRECTOS

1. **Service Worker Registrado**
   - Archivo: [static/js/sw.js](static/js/sw.js)
   - Ruta de servicio: `/sw.js` ([config/urls.py:18](config/urls.py#L18))
   - Listeners de push correctamente implementados

2. **PWA Manifests Dinámicos**
   - Admin: [base_admin.html:19](templates/admin_panel/base_admin.html#L19)
   - Cliente: [base_publica.html:19](templates/minipagina/base_publica.html#L19)
   - Generados dinámicamente por negocio

3. **VAPID Keys Configurados**
   - En archivo `.env`:
     - `VAPID_PRIVATE_KEY`
     - `VAPID_PUBLIC_KEY`
     - `VAPID_ADMIN_EMAIL`
   - Cargados en [config/settings/base.py](config/settings/base.py)

4. **API Endpoints para Push**
   - `/api/notificaciones/push/vapid-key/` - Obtener clave pública
   - `/api/notificaciones/push/subscribe/` - Suscribir cliente
   - `/api/notificaciones/push/subscribe-admin/` - Suscribir admin
   - `/api/notificaciones/push/test/` - Endpoint de prueba

5. **Servicio de Notificaciones**
   - [apps/notificaciones/services.py](apps/notificaciones/services.py)
   - Método `enviar_push()` correctamente implementado
   - Usa `pywebpush` para enviar notificaciones

6. **Badge API Implementado**
   - ✅ Contador automático en ícono de PWA
   - ✅ Incremento/decremento al recibir/click notificaciones
   - ✅ Auto-limpieza al enfocar la app

## Posibles Causas de que NO Lleguen las Notificaciones

### 1. Usuarios No Suscritos a Push Notifications

**Problema:** Los usuarios deben suscribirse explícitamente a las notificaciones push.

**Verificar:**
```javascript
// En la consola del navegador del usuario
navigator.serviceWorker.ready.then(registration => {
    registration.pushManager.getSubscription().then(subscription => {
        console.log('Suscrito:', subscription !== null);
        if (subscription) {
            console.log('Endpoint:', subscription.endpoint);
        }
    });
});
```

**Solución:**
- Asegurarse de que se llama a `PWA.requestNotificationPermission()` después de instalar la PWA
- Verificar que el usuario dio permiso de notificaciones
- Revisar que la suscripción se guardó en el servidor

### 2. Permisos de Notificaciones Denegados

**Problema:** El usuario puede haber denegado permisos de notificaciones.

**Verificar:**
```javascript
console.log('Permiso notificaciones:', Notification.permission);
// Debe ser "granted", no "denied" ni "default"
```

**Solución:**
- Si es "denied": El usuario debe ir a configuración del navegador y habilitar notificaciones manualmente
- Si es "default": Llamar a `Notification.requestPermission()`

### 3. Service Worker No Activo

**Problema:** El service worker puede no estar activo o registrado.

**Verificar:**
1. Abrir DevTools (F12)
2. Ir a **Application** > **Service Workers**
3. Verificar que aparece `/sw.js` como **activated**

**Solución:**
- Forzar actualización del service worker
- Verificar que no hay errores en la consola
- Hacer hard refresh (Ctrl+Shift+R)

### 4. Base de Datos de Suscripciones Vacía

**Problema:** Aunque el cliente se suscribe, la suscripción puede no haberse guardado en el servidor.

**Verificar en la consola de Django:**
```python
from apps.notificaciones.models import ClientePushSubscription, UsuarioPushSubscription

# Ver suscripciones de clientes
clientes = ClientePushSubscription.objects.filter(activa=True)
print(f"Suscripciones de clientes activas: {clientes.count()}")

# Ver suscripciones de admins
admins = UsuarioPushSubscription.objects.filter(activa=True)
print(f"Suscripciones de admins activas: {admins.count()}")
```

**Solución:**
- Verificar que el endpoint `/api/notificaciones/push/subscribe/` funciona
- Revisar logs del servidor para errores
- Asegurarse de que el teléfono del cliente se pasa correctamente

### 5. VAPID Keys Inválidas o Mal Configuradas

**Problema:** Las claves VAPID pueden estar mal formateadas o no coincidir.

**Verificar:**
```bash
# Ver las claves en .env
cat .env | grep VAPID

# Verificar que la clave pública es accesible
curl http://localhost:8000/api/notificaciones/push/vapid-key/
```

**Solución:**
- Generar nuevas claves VAPID si es necesario:
```python
from pywebpush import webpush
from py_vapid import Vapid01

vapid = Vapid01()
vapid.generate_keys()
print("VAPID_PRIVATE_KEY:", vapid.private_key.decode('utf-8'))
print("VAPID_PUBLIC_KEY:", vapid.public_key.decode('utf-8'))
```

### 6. Problemas de Red o Firewall

**Problema:** El servidor push puede estar bloqueado por firewall o problemas de red.

**Verificar:**
- Revisar logs del servidor para errores de `WebPushException`
- Verificar conectividad a internet
- En producción, verificar que el dominio usa HTTPS (requerido para push)

### 7. Testing en HTTP (No HTTPS)

**Problema:** Las notificaciones push requieren HTTPS en producción.

**Solución:**
- En desarrollo local: `localhost` está permitido
- En producción: DEBE usar HTTPS
- Verificar certificado SSL válido

### 8. Endpoint de Test Incompleto

**Problema:** El endpoint `/api/notificaciones/push/test/` tiene un TODO y no envía realmente.

**Ubicación:** [apps/notificaciones/push_views.py:246](apps/notificaciones/push_views.py#L246)

**Solución:** Implementar el endpoint de test completamente.

## Plan de Acción para Diagnosticar

### Paso 1: Verificar Configuración Básica

```bash
# 1. Verificar que el servidor está corriendo
# 2. Abrir la PWA en Chrome/Edge
# 3. Abrir DevTools (F12)
# 4. Ir a Console y ejecutar:
```

```javascript
// Verificar service worker
navigator.serviceWorker.ready.then(reg => {
    console.log('SW registrado:', reg);
    return reg.pushManager.getSubscription();
}).then(sub => {
    console.log('Suscripción:', sub);
    if (sub) {
        console.log('Endpoint:', sub.endpoint);
    } else {
        console.log('NO SUSCRITO - Este es el problema!');
    }
});

// Verificar permisos
console.log('Permiso notificaciones:', Notification.permission);

// Verificar Badge API
console.log('Badge API soportada:', 'setAppBadge' in navigator);
```

### Paso 2: Suscribirse Manualmente

Si no está suscrito, forzar suscripción:

```javascript
// Forzar suscripción
PWA.requestNotificationPermission().then(result => {
    console.log('Resultado:', result);
});

// Después de 5 segundos, verificar:
setTimeout(() => {
    navigator.serviceWorker.ready.then(reg => {
        return reg.pushManager.getSubscription();
    }).then(sub => {
        if (sub) {
            console.log('ÉXITO! Ahora estás suscrito');
            console.log('Endpoint:', sub.endpoint);
        } else {
            console.log('FALLO: Aún no suscrito. Ver errores arriba');
        }
    });
}, 5000);
```

### Paso 3: Verificar Base de Datos

En la consola de Django o shell:

```python
from apps.notificaciones.models import ClientePushSubscription
from apps.clientes.models import Cliente

# Ver todas las suscripciones
subs = ClientePushSubscription.objects.all()
print(f"Total suscripciones: {subs.count()}")

for sub in subs:
    print(f"Cliente: {sub.cliente.nombre} - Activa: {sub.activa} - Endpoint: {sub.endpoint[:50]}...")
```

### Paso 4: Enviar Notificación de Prueba Manualmente

```python
from apps.notificaciones.services import NotificacionService
from apps.clientes.models import Cliente

# Obtener un cliente con suscripción
cliente = Cliente.objects.first()

# Enviar notificación
service = NotificacionService()
result = service.enviar_push(
    cliente=cliente,
    titulo="Prueba de notificación",
    mensaje="Si ves esto, las notificaciones funcionan!"
)

print("Resultado:", result)
```

### Paso 5: Revisar Logs

```bash
# Ver logs en tiempo real
tail -f logs/django.log

# O si usas Railway/Heroku
railway logs --tail
# o
heroku logs --tail
```

Buscar errores relacionados con:
- `WebPushException`
- `pywebpush`
- `VAPID`
- `push notification`

## Checklist de Verificación

- [ ] Service worker registrado y activo
- [ ] Usuario dio permiso de notificaciones (Notification.permission = "granted")
- [ ] Usuario está suscrito a push (getSubscription() retorna objeto)
- [ ] Suscripción guardada en base de datos del servidor
- [ ] VAPID keys configuradas correctamente en .env
- [ ] Endpoint de VAPID key retorna la clave pública
- [ ] pywebpush está instalado (`pip list | grep webpush`)
- [ ] En producción: sitio usa HTTPS
- [ ] No hay errores en la consola del navegador
- [ ] No hay errores en logs del servidor

## Soluciones Rápidas

### Si las notificaciones nunca han funcionado:

1. **Verificar instalación de pywebpush:**
   ```bash
   pip install pywebpush
   ```

2. **Regenerar VAPID keys:**
   ```python
   from py_vapid import Vapid01
   vapid = Vapid01()
   vapid.generate_keys()
   # Copiar las claves al .env
   ```

3. **Forzar nueva suscripción:**
   - Ir a DevTools > Application > Storage > Clear storage
   - Recargar página
   - Volver a instalar PWA
   - Aceptar permisos de notificaciones

### Si las notificaciones funcionaban antes pero dejaron de funcionar:

1. **Verificar suscripciones expiradas:**
   ```python
   from apps.notificaciones.models import ClientePushSubscription
   # Desactivar todas y forzar re-suscripción
   ClientePushSubscription.objects.update(activa=False)
   ```

2. **Verificar cambios en VAPID keys:**
   - Las claves VAPID no deben cambiar
   - Si cambiaron, todos los usuarios deben re-suscribirse

## Próximos Pasos Recomendados

1. **Implementar endpoint de test completo** en [push_views.py:228](apps/notificaciones/push_views.py#L228)
2. **Agregar logging detallado** en [services.py](apps/notificaciones/services.py)
3. **Crear dashboard de diagnóstico** para admins
4. **Agregar banner de suscripción** más visible para usuarios
5. **Implementar re-suscripción automática** si la suscripción falla

## Recursos

- [Web Push Protocol](https://web.dev/push-notifications-overview/)
- [pywebpush Documentation](https://github.com/web-push-libs/pywebpush)
- [Service Workers MDN](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [Push API MDN](https://developer.mozilla.org/en-US/docs/Web/API/Push_API)

---

**Fecha:** 2026-09-04
**Estado:** Badge API implementado ✅ | Diagnóstico de Push completado ✅
**Próximo:** Ejecutar plan de diagnóstico paso a paso
