/**
 * Service Worker para PWA de FacilAdmin
 * Maneja caché, actualizaciones y funcionalidad offline
 * Versión optimizada para notificaciones en segundo plano
 */

// v5: deja de cachear páginas HTML (el activate borra la caché v4, que podía
// contener páginas privadas del panel del dueño)
const CACHE_NAME = 'faciladmin-v6';
const CACHE_ASSETS = [
    '/static/css/main.css',
    '/static/js/main.js',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
    'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css',
];

// Keep-alive: Mantener el Service Worker activo
// Esto ayuda a que las notificaciones lleguen más rápido
let keepAliveInterval = null;

function startKeepAlive() {
    if (keepAliveInterval) return;

    // Enviar un mensaje cada 20 segundos para mantener el SW activo
    keepAliveInterval = setInterval(() => {
        self.clients.matchAll({ includeUncontrolled: true, type: 'window' })
            .then((clients) => {
                if (clients.length > 0) {
                    // Hay clientes activos, mantener el SW despierto
                    console.log('[SW] Keep-alive ping');
                }
            });
    }, 20000); // 20 segundos
}

function stopKeepAlive() {
    if (keepAliveInterval) {
        clearInterval(keepAliveInterval);
        keepAliveInterval = null;
    }
}

// Instalar Service Worker y cachear assets
self.addEventListener('install', (event) => {
    console.log('[SW] Instalando Service Worker...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[SW] Cacheando archivos');
                // Intentar cachear pero no fallar si alguno no está disponible
                return cache.addAll(CACHE_ASSETS).catch((err) => {
                    console.log('[SW] Error cacheando algunos archivos:', err);
                });
            })
            .then(() => self.skipWaiting())
    );
});

// Activar Service Worker y limpiar cachés antiguos
self.addEventListener('activate', (event) => {
    console.log('[SW] Activando Service Worker...');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cache) => {
                    if (cache !== CACHE_NAME) {
                        console.log('[SW] Eliminando caché antiguo:', cache);
                        return caches.delete(cache);
                    }
                })
            );
        }).then(() => {
            // Iniciar keep-alive cuando se activa el SW
            startKeepAlive();
            console.log('[SW] Keep-alive iniciado');
            return self.clients.claim();
        })
    );
});

// Página mostrada al navegar sin conexión
const OFFLINE_HTML = `<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sin conexión</title>
<style>body{font-family:system-ui,sans-serif;display:flex;align-items:center;justify-content:center;
min-height:100vh;margin:0;padding:16px;text-align:center;background:#f5f5f5;color:#333}
button{margin-top:16px;padding:10px 20px;border:0;border-radius:8px;background:#667eea;color:#fff;font-size:16px}</style>
</head><body><div><h1>Sin conexión</h1><p>Revisa tu conexión a internet e intenta de nuevo.</p>
<button onclick="location.reload()">Reintentar</button></div></body></html>`;

// Estrategia:
// - Páginas (navegación) y APIs: siempre red, nunca se guardan en caché.
//   Así la sesión se valida en cada apertura y no quedan páginas privadas
//   del panel guardadas en el dispositivo.
// - Archivos estáticos (/static/): red primero y copia en caché para offline.
self.addEventListener('fetch', (event) => {
    // Ignorar requests que no sean GET
    if (event.request.method !== 'GET') {
        return;
    }

    // Ignorar requests a APIs externas (Google Analytics, etc.)
    if (!event.request.url.startsWith(self.location.origin)) {
        return;
    }

    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request).catch(() => new Response(OFFLINE_HTML, {
                headers: { 'Content-Type': 'text/html; charset=utf-8' }
            }))
        );
        return;
    }

    // Solo los archivos estáticos se guardan en caché
    if (!new URL(event.request.url).pathname.startsWith('/static/')) {
        return;
    }

    event.respondWith(
        fetch(event.request)
            .then((response) => {
                // Si la respuesta es válida, clonarla y guardarla en caché
                if (response && response.status === 200) {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, responseClone);
                    });
                }
                return response;
            })
            .catch(() => {
                // Si falla la red, intentar desde caché
                return caches.match(event.request).then((cachedResponse) => {
                    if (cachedResponse) {
                        return cachedResponse;
                    }

                    // No está en caché: retornar error
                    return new Response('Offline', {
                        status: 503,
                        statusText: 'Service Unavailable'
                    });
                });
            })
    );
});

// Escuchar mensajes desde el cliente
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }

    // Manejar mensajes de badge
    if (event.data && event.data.type === 'CLEAR_BADGE') {
        clearBadge();
    }

    if (event.data && event.data.type === 'SET_BADGE') {
        const count = event.data.count || 0;
        saveBadgeCount(count);
    }
});

// Push Notifications
self.addEventListener('push', (event) => {
    console.log('[SW] Push recibido:', event);

    // Reiniciar keep-alive si estaba detenido
    startKeepAlive();

    if (!event.data) {
        console.log('[SW] Push sin datos');
        // Mostrar notificación genérica aunque no haya datos
        event.waitUntil(
            Promise.all([
                self.registration.showNotification('FacilAdmin', {
                    body: 'Tienes una nueva notificación',
                    icon: '/static/images/faciladmin-logo.png',
                    badge: '/static/images/faciladmin-logo.png',
                    vibrate: [200, 100, 200]
                }),
                incrementBadge()
            ])
        );
        return;
    }

    try {
        const data = event.data.json();
        console.log('[SW] Datos del push:', data);

        const title = data.title || data.head || 'FacilAdmin';
        const options = {
            body: data.body || data.message || '',
            icon: data.icon || '/static/images/faciladmin-logo.png',
            badge: data.badge || '/static/images/faciladmin-logo.png',
            // Sin tag por defecto: cada notificación se muestra por separado
            // (con un tag común se reemplazaban y solo quedaba la última)
            ...(data.tag ? { tag: data.tag, renotify: true } : {}),
            requireInteraction: data.requireInteraction || false,
            vibrate: data.vibrate || [200, 100, 200],
            data: {
                url: data.url || data.link || '/',
                citaId: data.citaId || null,
                tipo: data.tipo || 'general',
                // Enlace del botón "WhatsApp" (acción 'whatsapp')
                whatsapp: data.whatsapp || null
            },
            actions: data.actions || [],
            // Agregar timestamp para que cada notificación sea única
            timestamp: Date.now()
        };

        event.waitUntil(
            Promise.all([
                // Si reemplaza una notificación visible de la misma cita, no sumar
                // al contador (debe coincidir con lo que se ve en la bandeja)
                (data.tag
                    ? self.registration.getNotifications({ tag: data.tag })
                    : Promise.resolve([])
                ).then((previas) => Promise.all([
                    self.registration.showNotification(title, options),
                    previas.length ? null : incrementBadge()
                ])),
                // Notificar a los clientes activos que llegó una notificación
                notifyClients({
                    type: 'PUSH_RECEIVED',
                    data: data
                })
            ])
        );
    } catch (error) {
        console.error('[SW] Error procesando push:', error);
        // Mostrar notificación genérica en caso de error
        event.waitUntil(
            Promise.all([
                self.registration.showNotification('Nueva notificación', {
                    body: 'Tienes una nueva actualización',
                    icon: '/static/images/faciladmin-logo.png',
                    timestamp: Date.now()
                }),
                incrementBadge()
            ])
        );
    }
});

/**
 * Notifica a todos los clientes activos
 */
async function notifyClients(message) {
    try {
        const clients = await self.clients.matchAll({ includeUncontrolled: true, type: 'window' });
        clients.forEach(client => {
            client.postMessage(message);
        });
    } catch (error) {
        console.error('[SW] Error notificando a clientes:', error);
    }
}

// Manejar click en notificaciones
/**
 * ¿La ventana pertenece a la app de este Service Worker?
 * - Panel del dueño: alcance /<negocio>/admin/
 * - Mini-página:     alcance /<negocio>/ sin incluir /<negocio>/admin/,
 *   que está dentro de su ruta pero es la otra app
 */
function esDeEstaApp(url) {
    const alcance = self.registration.scope;
    if (!url.startsWith(alcance)) {
        return false;
    }
    if (alcance.endsWith('/admin/')) {
        return true;
    }
    return !url.startsWith(`${alcance}admin/`);
}

self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    // Botón "WhatsApp": abrir el chat con el mensaje prellenado
    const datos = event.notification.data || {};
    if (event.action === 'whatsapp' && datos.whatsapp) {
        event.waitUntil(Promise.all([
            decrementBadge(),
            clients.openWindow(datos.whatsapp)
        ]));
        return;
    }

    // URL absoluta: client.url es absoluta, así se puede comparar y reutilizar la ventana
    const urlToOpen = new URL((event.notification.data && event.notification.data.url) || '/', self.location.origin).href;

    event.waitUntil(
        Promise.all([
            decrementBadge(),
            clients.matchAll({ type: 'window', includeUncontrolled: true })
                .then((todas) => {
                    // Solo ventanas de ESTA app. matchAll devuelve todas las del
                    // sitio, incluida la otra app instalada del mismo negocio: antes
                    // un aviso del cliente podía abrirse dentro de la app del dueño
                    // (p. ej. si esta estaba en la página de login).
                    const clientList = todas.filter((c) => esDeEstaApp(c.url));

                    // Si ya está abierta exactamente esa página, enfocarla
                    const exacta = clientList.find((c) => c.url === urlToOpen && 'focus' in c);
                    if (exacta) {
                        return exacta.focus();
                    }
                    // Si esta app está abierta en otra pantalla, llevarla a la
                    // página de la notificación
                    const misma = clientList.find((c) => 'navigate' in c);
                    if (misma) {
                        return misma.navigate(urlToOpen).then((c) => (c || misma).focus());
                    }
                    // Si no, abrir nueva ventana
                    if (clients.openWindow) {
                        return clients.openWindow(urlToOpen);
                    }
                })
        ])
    );
});

// ============================================
// Badge API - Contador de notificaciones
// ============================================

/**
 * Incrementa el contador de badge en 1
 */
async function incrementBadge() {
    try {
        if ('setAppBadge' in navigator) {
            // Obtener el count actual del IndexedDB o usar 0
            const currentBadge = await getBadgeCount();
            const newBadge = currentBadge + 1;

            // Actualizar el badge
            await navigator.setAppBadge(newBadge);

            // Guardar el nuevo count
            await saveBadgeCount(newBadge);

            console.log('[SW] Badge incrementado a:', newBadge);
        } else {
            console.log('[SW] Badge API no soportada');
        }
    } catch (error) {
        console.error('[SW] Error incrementando badge:', error);
    }
}

/**
 * Decrementa el contador de badge en 1
 */
async function decrementBadge() {
    try {
        if ('clearAppBadge' in navigator) {
            const currentBadge = await getBadgeCount();
            const newBadge = Math.max(0, currentBadge - 1);

            if (newBadge === 0) {
                // Si llegó a 0, limpiar el badge
                await navigator.clearAppBadge();
            } else {
                // Si todavía hay notificaciones, actualizar el número
                await navigator.setAppBadge(newBadge);
            }

            // Guardar el nuevo count
            await saveBadgeCount(newBadge);

            console.log('[SW] Badge decrementado a:', newBadge);
        }
    } catch (error) {
        console.error('[SW] Error decrementando badge:', error);
    }
}

/**
 * Limpia el badge completamente
 */
async function clearBadge() {
    try {
        if ('clearAppBadge' in navigator) {
            await navigator.clearAppBadge();
            await saveBadgeCount(0);
            console.log('[SW] Badge limpiado');
        }
    } catch (error) {
        console.error('[SW] Error limpiando badge:', error);
    }
}

/**
 * Obtiene el count actual del badge desde IndexedDB
 */
async function getBadgeCount() {
    try {
        const db = await openBadgeDB();
        return new Promise((resolve, reject) => {
            const transaction = db.transaction(['badge'], 'readonly');
            const store = transaction.objectStore('badge');
            const request = store.get('count');

            request.onsuccess = () => {
                resolve(request.result ? request.result.value : 0);
            };

            request.onerror = () => {
                reject(request.error);
            };
        });
    } catch (error) {
        console.error('[SW] Error obteniendo badge count:', error);
        return 0;
    }
}

/**
 * Guarda el count del badge en IndexedDB
 */
async function saveBadgeCount(count) {
    try {
        const db = await openBadgeDB();
        return new Promise((resolve, reject) => {
            const transaction = db.transaction(['badge'], 'readwrite');
            const store = transaction.objectStore('badge');
            const request = store.put({ id: 'count', value: count });

            request.onsuccess = () => {
                resolve();
            };

            request.onerror = () => {
                reject(request.error);
            };
        });
    } catch (error) {
        console.error('[SW] Error guardando badge count:', error);
    }
}

/**
 * Abre la base de datos IndexedDB para el badge
 */
function openBadgeDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('FacilAdminBadge', 1);

        request.onerror = () => {
            reject(request.error);
        };

        request.onsuccess = () => {
            resolve(request.result);
        };

        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains('badge')) {
                db.createObjectStore('badge', { keyPath: 'id' });
            }
        };
    });
}
