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
    navigator.serviceWorker.register('/static/js/sw.js', { scope: '/' })
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
 * Muestra el banner de instalación
 */
function showInstallBanner() {
    const banner = document.getElementById('install-banner');
    if (banner) {
        banner.style.display = 'block';
    }
}

/**
 * Oculta el banner de instalación
 */
function hideInstallBanner() {
    const banner = document.getElementById('install-banner');
    if (banner) {
        banner.style.display = 'none';
    }
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
        return true;
    } else {
        console.log('[PWA] Permisos de notificación denegados');
        return false;
    }
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
    hideInstallBanner
};
