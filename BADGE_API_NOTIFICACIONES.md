# Badge API - Contador de Notificaciones PWA

## Resumen de la Implementación

> **Importante — Android:** Chrome para Android **no soporta** `navigator.setAppBadge`.
> En Android el número del ícono lo calcula el launcher (MIUI, One UI, Pixel...)
> contando las notificaciones que **esa app instalada** tiene en la bandeja.
> Para que se asignen a la app (y no a Chrome), el Service Worker debe tener
> el **mismo alcance** que la app instalada (ver "Alcance del Service Worker").

Se ha implementado el **Badge API** para mostrar un contador de notificaciones en el ícono de la PWA instalada, similar al comportamiento de las aplicaciones de redes sociales.

## Archivos Modificados

### 1. [static/js/sw.js](static/js/sw.js)
**Service Worker - Gestión del Badge**

Se agregaron las siguientes funcionalidades:

#### Incrementar Badge al Recibir Notificación
- Cuando llega una notificación push, el contador se incrementa automáticamente
- El contador se guarda en IndexedDB para persistencia

#### Decrementar Badge al Hacer Click
- Cuando el usuario hace click en una notificación, el contador se decrementa
- Si el contador llega a 0, el badge se limpia completamente

#### Funciones de Gestión del Badge
- `incrementBadge()`: Incrementa el contador en 1
- `decrementBadge()`: Decrementa el contador en 1
- `clearBadge()`: Limpia el badge completamente
- `getBadgeCount()`: Obtiene el contador actual desde IndexedDB
- `saveBadgeCount(count)`: Guarda el contador en IndexedDB
- `openBadgeDB()`: Abre la base de datos IndexedDB para el badge

### 2. [static/js/pwa-register.js](static/js/pwa-register.js)
**Registro PWA - Control del Badge desde el Cliente**

Se agregaron funciones para controlar el badge desde el cliente:

#### Nuevas Funciones Exportadas
- `clearNotificationBadge()`: Limpia el badge desde el cliente
- `setNotificationBadge(count)`: Actualiza el badge a un número específico

#### Auto-limpieza del Badge
- Al abrir la app instalada o volver a ella, el badge se limpia después de 2 segundos
  (eventos `pageshow` y `visibilitychange`; `focus` casi nunca se dispara al abrir desde el ícono)
- Esto simula el comportamiento de apps como WhatsApp o Telegram

#### Agrupación de notificaciones (tag)
- Las notificaciones de una **misma cita** (nueva, editada, cancelada) usan el tag `cita-<id>`
  y se reemplazan entre sí; en ese caso el contador **no** se incrementa
- Las de citas distintas se acumulan en la bandeja, cada una con su +1
- Sin cita no hay tag: cada notificación se muestra por separado

#### Al tocar la notificación
- Dueño: abre `/<slug>/admin/agenda/`
- Cliente: abre `/<slug>/mis-citas/`
- Si la app ya está abierta en otra pantalla, se navega a esa página en vez de abrir otra ventana

### 3. Templates
Los templates ya tenían configurado:
- ✓ Manifests dinámicos ([base_admin.html](templates/admin_panel/base_admin.html#L19) y [base_publica.html](templates/minipagina/base_publica.html#L19))
- ✓ Service Worker registrado ([pwa-register.js](static/js/pwa-register.js#L18))
- ✓ Meta tags para PWA

## Alcance del Service Worker

Cada app instalada registra su propio Service Worker (`/sw.js`) con el mismo
alcance que su manifest:

| App | Alcance (manifest y Service Worker) |
|-----|-------------------------------------|
| Panel del dueño | `/<negocio>/admin/` |
| Mini-página (cliente) | `/<negocio>/` |

Las plantillas lo indican con `window.PWA_SCOPE` antes de cargar `pwa-register.js`.

- Android asigna cada notificación a la app cuyo alcance contiene el del Service
  Worker. Con el alcance anterior (`/`, todo el sitio) no coincidía con ninguna
  app: las notificaciones aparecían como de **Chrome** y el contador se sumaba
  al ícono de Chrome.
- Panel y mini-página tienen suscripciones push separadas aunque estén en el
  mismo navegador.
- Migración: al abrir la app se elimina el Service Worker antiguo de alcance `/`
  y su suscripción; el servidor desactiva esa suscripción cuando Google responde 410.
- Al abrir la app se cierran sus notificaciones de la bandeja, así el contador
  de Android vuelve a cero (como WhatsApp).

## Entrega de los push

Los push se envían con `ttl` de 24 horas y `Urgency: high`
(`OPCIONES_ENTREGA_PUSH` en `apps/notificaciones/services.py`). Con el valor por
defecto de pywebpush (TTL 0), Google descartaba el mensaje si el celular estaba
en reposo.

**Xiaomi (MIUI) y otros con ahorro de batería agresivo:** si las notificaciones
no llegan aunque el permiso esté concedido, en *Ajustes → Aplicaciones → Chrome*
poner **Ahorro de batería: Sin restricciones** (y activar *Inicio automático*).

## Cómo Funciona

### Flujo de Notificaciones

```
1. Servidor envía notificación push
   ↓
2. Service Worker recibe el push (sw.js:103)
   ↓
3. Se incrementa el badge en el ícono (+1)
   ↓
4. Se muestra la notificación al usuario
   ↓
5. Usuario hace click en la notificación
   ↓
6. Se decrementa el badge (-1)
   ↓
7. Si badge = 0, se limpia completamente
```

### Flujo de Auto-limpieza

```
1. Usuario instala la PWA
   ↓
2. Usuario abre la app (evento focus)
   ↓
3. Espera 2 segundos
   ↓
4. Badge se limpia automáticamente
```

## Pruebas Locales

### 1. Verificar que el Service Worker está Registrado

1. Abre la consola del navegador (F12)
2. Ve a la pestaña **Application** > **Service Workers**
3. Deberías ver el service worker registrado en `/sw.js`

### 2. Verificar Badge API Support

Ejecuta en la consola:
```javascript
console.log('Badge API soportada:', 'setAppBadge' in navigator);
```

**Nota:** El Badge API solo está soportado en:
- ⚠️ Android: no hay `setAppBadge`; el launcher muestra el número de notificaciones de la app
- ✅ Chrome/Edge 81+ en Windows/macOS (solo en PWA instalada)
- ✅ iPhone/iPad con iOS 16.4+ (solo app instalada en pantalla de inicio y con permiso de notificaciones)
- ❌ Firefox (no soportado)

### 3. Probar Incremento Manual del Badge

Ejecuta en la consola:
```javascript
// Establecer badge en 5
navigator.setAppBadge(5);

// Limpiar badge
navigator.clearAppBadge();
```

### 4. Probar Notificación Push Completa

#### Opción A: Usar el API de Test

Si existe un endpoint de prueba:
```bash
# Desde el navegador o Postman
POST http://localhost:8000/api/notificaciones/push/test/
```

#### Opción B: Enviar Push Manualmente

1. Instala la PWA en tu dispositivo
2. Suscríbete a notificaciones push
3. Agenda una cita para que se envíe una notificación
4. Verifica que:
   - ✅ La notificación aparece
   - ✅ El badge se incrementa en el ícono de la app
   - ✅ Al hacer click, el badge se decrementa

### 5. Verificar Auto-limpieza

1. Genera varias notificaciones (badge debe tener un número)
2. Abre la PWA instalada
3. Espera 2-3 segundos
4. El badge debe limpiarse automáticamente

## Debugging

### Ver Logs del Service Worker

1. Abre DevTools (F12)
2. Ve a **Console**
3. Filtra por `[SW]` para ver solo los logs del service worker

### Ver Base de Datos IndexedDB

1. Abre DevTools (F12)
2. Ve a **Application** > **Storage** > **IndexedDB**
3. Busca la base de datos `FacilAdminBadge`
4. Verás el contador actual en el object store `badge`

### Errores Comunes

#### Badge no aparece
- Verifica que la PWA esté instalada (no funciona en navegador normal)
- Verifica soporte del navegador (Chrome/Edge en Android o Desktop)
- Verifica que no haya errores en la consola

#### Badge no se limpia
- Verifica que `clearAppBadge` esté disponible en el navegador
- Verifica los logs del service worker
- Revisa que IndexedDB esté accesible

#### Notificaciones no llegan
- Verifica permisos de notificaciones
- Verifica que el service worker esté activo
- Verifica VAPID keys en `.env`
- Revisa los logs del servidor Python

## Uso desde el Código

### Limpiar Badge Manualmente
```javascript
// Desde cualquier página donde se cargue pwa-register.js
PWA.clearNotificationBadge();
```

### Establecer Badge a un Número Específico
```javascript
// Por ejemplo, si tienes 3 notificaciones sin leer
PWA.setNotificationBadge(3);
```

### Verificar si la PWA está Instalada
```javascript
if (PWA.isPWAInstalled()) {
    console.log('Usuario tiene la PWA instalada');
}
```

## Compatibilidad

| Plataforma | Soporte | Notas |
|-----------|---------|-------|
| Chrome Android | ⚠️ Vía launcher | No soporta setAppBadge: el launcher cuenta las notificaciones de la app |
| Edge Android | ⚠️ Vía launcher | Igual que Chrome Android |
| Chrome Desktop | ✅ Sí | Solo PWA instalada |
| Edge Desktop | ✅ Sí | Solo PWA instalada |
| Safari iOS / iPadOS | ✅ Sí | iOS 16.4+, solo app en pantalla de inicio con permiso de notificaciones |
| Firefox | ❌ No | No soportado |

## Recursos

- [MDN: Badge API](https://developer.mozilla.org/en-US/docs/Web/API/Badging_API)
- [Chrome Developers: Badging API](https://web.dev/badging-api/)
- [Can I Use: Badge API](https://caniuse.com/mdn-api_navigator_setappbadge)

## Próximos Pasos

1. ✅ Badge API implementado
2. ⏳ Probar en dispositivos reales (Android con Chrome)
3. ⏳ Verificar que las notificaciones llegan correctamente
4. ⏳ Ajustar el tiempo de auto-limpieza si es necesario (actualmente 2s)

---

**Fecha de implementación:** 2026-09-04
**Desarrollador:** Claude Code
