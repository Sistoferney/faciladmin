/**
 * Service Worker para PWA de FacilAdmin
 * Maneja caché, actualizaciones y funcionalidad offline
 * Versión optimizada para notificaciones en segundo plano
 */

const CACHE_NAME = 'faciladmin-v2';
const CACHE_ASSETS = [
    '/',
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

// Estrategia: Network First, luego Cache (para contenido dinámico)
self.addEventListener('fetch', (event) => {
    // Ignorar requests que no sean GET
    if (event.request.method !== 'GET') {
        return;
    }

    // Ignorar requests a APIs externas (Google Analytics, etc.)
    if (!event.request.url.startsWith(self.location.origin)) {
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

                    // Si no está en caché y es una navegación, mostrar página offline
                    if (event.request.mode === 'navigate') {
                        return caches.match('/offline.html');
                    }

                    // Para otros recursos, retornar error
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
            tag: data.tag || 'faciladmin-notification',
            requireInteraction: data.requireInteraction || false,
            vibrate: data.vibrate || [200, 100, 200],
            data: {
                url: data.url || data.link || '/',
                citaId: data.citaId || null,
                tipo: data.tipo || 'general'
            },
            actions: data.actions || [],
            // Agregar timestamp para que cada notificación sea única
            timestamp: Date.now()
        };

        event.waitUntil(
            Promise.all([
                self.registration.showNotification(title, options),
                incrementBadge(),
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
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    const urlToOpen = event.notification.data.url || '/';

    event.waitUntil(
        Promise.all([
            decrementBadge(),
            clients.matchAll({ type: 'window', includeUncontrolled: true })
                .then((clientList) => {
                    // Si ya hay una ventana abierta, enfocarla
                    for (let i = 0; i < clientList.length; i++) {
                        const client = clientList[i];
                        if (client.url === urlToOpen && 'focus' in client) {
                            return client.focus();
                        }
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
