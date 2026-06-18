/**
 * Service Worker para PWA de FacilAdmin
 * Maneja caché, actualizaciones y funcionalidad offline
 */

const CACHE_NAME = 'faciladmin-v1';
const CACHE_ASSETS = [
    '/',
    '/static/css/main.css',
    '/static/js/main.js',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
    'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css',
];

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
        }).then(() => self.clients.claim())
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
});

// Push Notifications
self.addEventListener('push', (event) => {
    console.log('[SW] Push recibido:', event);

    if (!event.data) {
        console.log('[SW] Push sin datos');
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
            actions: data.actions || []
        };

        event.waitUntil(
            self.registration.showNotification(title, options)
        );
    } catch (error) {
        console.error('[SW] Error procesando push:', error);
        // Mostrar notificación genérica en caso de error
        event.waitUntil(
            self.registration.showNotification('Nueva notificación', {
                body: 'Tienes una nueva actualización',
                icon: '/static/images/faciladmin-logo.png'
            })
        );
    }
});

// Manejar click en notificaciones
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    const urlToOpen = event.notification.data.url || '/';

    event.waitUntil(
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
    );
});
