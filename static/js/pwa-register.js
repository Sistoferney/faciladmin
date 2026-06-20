/**
 * Registro y gestión de PWA
 * Registra el Service Worker y maneja la instalación
 */

// Detectar si el navegador soporta PWA
if ('serviceWorker' in navigator) {
    // Registrar Service Worker cuando la página cargue
    window.addEventListener('load', () => {
        registerServiceWorker();
    });
}

/**
 * Registra el Service Worker
 */
function registerServiceWorker() {
    navigator.serviceWorker.register('/sw.js', { scope: '/' })
        .then((registration) => {
            console.log('[PWA] Service Worker registrado:', registration.scope);

            // Verificar actualizaciones periódicamente
            setInterval(() => {
                registration.update();
            }, 60000); // Cada minuto

            // Manejar actualizaciones del SW
            registration.addEventListener('updatefound', () => {
                const newWorker = registration.installing;
                newWorker.addEventListener('statechange', () => {
                    if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                        // Hay una nueva versión disponible
                        if (confirm('Hay una nueva versión disponible. ¿Recargar para actualizar?')) {
                            newWorker.postMessage({ type: 'SKIP_WAITING' });
                            window.location.reload();
                        }
                    }
                });
            });
        })
        .catch((error) => {
            console.error('[PWA] Error registrando Service Worker:', error);
        });

    // Recargar cuando el nuevo SW tome control
    navigator.serviceWorker.addEventListener('controllerchange', () => {
        window.location.reload();
    });
}

/**
 * Detecta si la app está instalada (modo standalone)
 */
function isPWAInstalled() {
    // Verificar si está en modo standalone
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches;

    // Verificar en iOS
    const isIOSStandalone = window.navigator.standalone === true;

    return isStandalone || isIOSStandalone;
}

/**
 * Guarda si el usuario tiene la PWA instalada
 */
if (isPWAInstalled()) {
    localStorage.setItem('pwa_installed', 'true');
    console.log('[PWA] App instalada en modo standalone');
} else {
    localStorage.setItem('pwa_installed', 'false');
}

/**
 * Manejo del evento beforeinstallprompt
 * Este evento se dispara cuando el navegador detecta que la app es instalable
 */
let deferredPrompt = null;

window.addEventListener('beforeinstallprompt', (e) => {
    console.log('[PWA] beforeinstallprompt disparado');

    // Prevenir el prompt automático
    e.preventDefault();

    // Guardar el evento para usarlo después
    deferredPrompt = e;

    // Disparar evento personalizado para que los componentes lo manejen
    window.dispatchEvent(new CustomEvent('pwa-installable'));

    // Mostrar banner de instalación si no está instalada
    if (!isPWAInstalled()) {
        showInstallBanner();
    }
});

/**
 * Detecta si es un dispositivo iOS
 */
function isIOS() {
    const userAgent = window.navigator.userAgent.toLowerCase();
    return /iphone|ipad|ipod/.test(userAgent);
}

/**
 * Muestra el banner de instalación
 */
function showInstallBanner() {
    // En iOS, mostrar banner especial con instrucciones
    if (isIOS()) {
        const iosBanner = document.getElementById('install-banner-ios');
        if (iosBanner && !isPWAInstalled()) {
            iosBanner.style.display = 'block';
        }
    } else {
        // Android/Chrome: banner normal
        const banner = document.getElementById('install-banner');
        if (banner) {
            banner.style.display = 'block';
        }
    }
}

/**
 * Oculta el banner de instalación
 */
function hideInstallBanner() {
    const banner = document.getElementById('install-banner');
    const iosBanner = document.getElementById('install-banner-ios');

    if (banner) {
        banner.style.display = 'none';
    }
    if (iosBanner) {
        iosBanner.style.display = 'none';
    }

    // Guardar preferencia para no mostrar más
    localStorage.setItem('pwa_banner_dismissed', 'true');
}

/**
 * Muestra el prompt de instalación
 */
async function promptInstall() {
    if (!deferredPrompt) {
        console.log('[PWA] No hay prompt disponible');
        return;
    }

    // Mostrar el prompt
    deferredPrompt.prompt();

    // Esperar la respuesta del usuario
    const { outcome } = await deferredPrompt.userChoice;
    console.log('[PWA] Resultado de instalación:', outcome);

    if (outcome === 'accepted') {
        console.log('[PWA] Usuario aceptó instalar');
        hideInstallBanner();

        // Registrar para notificaciones push si está disponible
        if ('Notification' in window && 'PushManager' in window) {
            requestNotificationPermission();
        }
    } else {
        console.log('[PWA] Usuario rechazó instalar');
    }

    // Limpiar el prompt
    deferredPrompt = null;
}

/**
 * Solicita permiso para notificaciones push
 */
async function requestNotificationPermission() {
    if (Notification.permission === 'granted') {
        console.log('[PWA] Permisos de notificación ya concedidos');
        // Suscribirse a push notifications
        await subscribeToPushNotifications();
        return true;
    }

    if (Notification.permission === 'denied') {
        console.log('[PWA] Permisos de notificación denegados');
        return false;
    }

    // Solicitar permiso
    const permission = await Notification.requestPermission();

    if (permission === 'granted') {
        console.log('[PWA] Permisos de notificación concedidos');
        // Suscribirse a push notifications
        await subscribeToPushNotifications();
        return true;
    } else {
        console.log('[PWA] Permisos de notificación denegados');
        return false;
    }
}

/**
 * Se suscribe a notificaciones push
 */
async function subscribeToPushNotifications() {
    try {
        // Verificar soporte
        if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
            console.log('[PWA] Push notifications no soportadas');
            return null;
        }

        // Obtener registro del Service Worker
        const registration = await navigator.serviceWorker.ready;

        // Verificar si ya está suscrito
        let subscription = await registration.pushManager.getSubscription();

        if (subscription) {
            console.log('[PWA] Ya está suscrito a push notifications');
            return subscription;
        }

        // Obtener clave pública VAPID del servidor
        const response = await fetch('/api/notificaciones/push/vapid-key/');
        const data = await response.json();
        const publicKey = data.publicKey;

        if (!publicKey) {
            console.error('[PWA] No se pudo obtener la clave VAPID');
            return null;
        }

        // Convertir clave VAPID a formato Uint8Array
        const applicationServerKey = urlBase64ToUint8Array(publicKey);

        // Suscribirse
        subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: applicationServerKey
        });

        console.log('[PWA] Suscrito a push notifications:', subscription);

        // Enviar suscripción al servidor
        await savePushSubscription(subscription);

        return subscription;

    } catch (error) {
        console.error('[PWA] Error suscribiéndose a push:', error);
        return null;
    }
}

/**
 * Guarda la suscripción en el servidor
 */
async function savePushSubscription(subscription) {
    try {
        const response = await fetch('/api/notificaciones/push/subscribe/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                subscription: subscription.toJSON(),
                negocio_slug: window.location.pathname.split('/')[1] || null
            })
        });

        const data = await response.json();

        if (data.success) {
            console.log('[PWA] Suscripción guardada en servidor');
            localStorage.setItem('push_subscribed', 'true');
        } else {
            console.error('[PWA] Error guardando suscripción:', data.error);
        }

        return data.success;

    } catch (error) {
        console.error('[PWA] Error guardando suscripción:', error);
        return false;
    }
}

/**
 * Convierte una clave VAPID de Base64 a Uint8Array
 */
function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
        .replace(/\-/g, '+')
        .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}

/**
 * Evento cuando la app se instala
 */
window.addEventListener('appinstalled', () => {
    console.log('[PWA] App instalada exitosamente');
    hideInstallBanner();
    localStorage.setItem('pwa_installed', 'true');

    // Opcional: Enviar analytics
    // gtag('event', 'pwa_installed');
});

// Exportar funciones para uso global
window.PWA = {
    promptInstall,
    isPWAInstalled,
    requestNotificationPermission,
    subscribeToPushNotifications,
    hideInstallBanner
};
