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
                console.log('[PWA] Nueva versión detectada');

                newWorker.addEventListener('statechange', () => {
                    if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                        // Hay una nueva versión disponible
                        console.log('[PWA] Nueva versión lista para instalar');

                        // Mostrar notificación más amigable
                        const mensaje = 'Nueva actualización disponible con mejoras y correcciones. ¿Actualizar ahora?';

                        if (confirm(mensaje)) {
                            console.log('[PWA] Usuario aceptó actualización');
                            newWorker.postMessage({ type: 'SKIP_WAITING' });
                            window.location.reload();
                        } else {
                            console.log('[PWA] Usuario pospuso actualización');
                            // Mostrar banner persistente (opcional)
                            showUpdateBanner();
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
 * Inicializar banner en iOS cuando cargue la página
 * En iOS no existe beforeinstallprompt, así que mostramos el banner directamente
 */
window.addEventListener('load', () => {
    // Verificar si ya fue descartado
    const bannerDismissed = localStorage.getItem('pwa_banner_dismissed');

    if (!bannerDismissed && isIOS() && !isPWAInstalled()) {
        // Esperar un poco para que el DOM esté listo
        setTimeout(() => {
            showInstallBanner();
        }, 1000);
    }
});

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
 * Muestra un banner persistente de actualización disponible
 */
function showUpdateBanner() {
    // Verificar si ya existe el banner
    if (document.getElementById('update-banner')) {
        return;
    }

    // Crear banner de actualización
    const banner = document.createElement('div');
    banner.id = 'update-banner';
    banner.style.cssText = `
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 25px;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        z-index: 10000;
        display: flex;
        align-items: center;
        gap: 15px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        max-width: 90%;
    `;

    banner.innerHTML = `
        <span>🎉 Nueva actualización disponible</span>
        <button onclick="window.location.reload()" style="
            background: white;
            color: #667eea;
            border: none;
            padding: 8px 20px;
            border-radius: 5px;
            font-weight: bold;
            cursor: pointer;
        ">Actualizar</button>
        <button onclick="this.parentElement.remove()" style="
            background: transparent;
            color: white;
            border: 1px solid white;
            padding: 8px 15px;
            border-radius: 5px;
            cursor: pointer;
        ">Después</button>
    `;

    document.body.appendChild(banner);
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
        // Obtener teléfono del cliente (puede estar en localStorage o sessionStorage)
        // después de que el cliente agendó una cita
        const telefono = localStorage.getItem('cliente_telefono') ||
                        sessionStorage.getItem('cliente_telefono') ||
                        null;

        // Obtener slug del negocio de la URL
        const negocio_slug = window.location.pathname.split('/')[1] || null;

        // Detectar si es un administrador (está en /admin/)
        const esAdmin = window.location.pathname.includes('/admin/');

        // Para administradores, no necesitamos teléfono de cliente
        if (esAdmin && negocio_slug) {
            console.log('[PWA] Guardando suscripción para administrador');
            console.log('[PWA] Negocio slug:', negocio_slug);

            const response = await fetch('/api/notificaciones/push/subscribe-admin/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    subscription: subscription.toJSON(),
                    negocio_slug: negocio_slug  // Enviar slug del negocio
                })
            });

            const data = await response.json();

            if (data.success) {
                console.log('[PWA] Suscripción de admin guardada en servidor');
                console.log('[PWA] Negocio:', data.negocio);
                localStorage.setItem('push_subscribed', 'true');
                localStorage.setItem('push_negocio', negocio_slug);
                localStorage.setItem('push_es_admin', 'true');
            } else {
                console.error('[PWA] Error guardando suscripción de admin:', data.error);
            }

            return data.success;
        }

        // Para clientes, validar que tengamos teléfono y negocio
        if (!telefono || !negocio_slug) {
            console.warn('[PWA] No se puede guardar suscripción de cliente: falta teléfono o negocio_slug');
            console.warn('[PWA] Teléfono:', telefono, 'Negocio:', negocio_slug);

            // Guardar suscripción en localStorage para intentar más tarde
            localStorage.setItem('pending_push_subscription', JSON.stringify(subscription.toJSON()));

            return false;
        }

        const response = await fetch('/api/notificaciones/push/subscribe/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                subscription: subscription.toJSON(),
                telefono: telefono,
                negocio_slug: negocio_slug
            })
        });

        const data = await response.json();

        if (data.success) {
            console.log('[PWA] Suscripción guardada en servidor');
            localStorage.setItem('push_subscribed', 'true');
            // Limpiar suscripción pendiente si existía
            localStorage.removeItem('pending_push_subscription');
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

    // Solicitar permisos de notificación después de instalar
    // Dar un pequeño delay para mejor UX
    setTimeout(() => {
        if ('Notification' in window && 'PushManager' in window) {
            requestNotificationPermission();
        }
    }, 1000); // 1 segundo de delay

    // Opcional: Enviar analytics
    // gtag('event', 'pwa_installed');
});

/**
 * Limpia el badge de notificaciones
 */
async function clearNotificationBadge() {
    try {
        if ('clearAppBadge' in navigator) {
            await navigator.clearAppBadge();
            console.log('[PWA] Badge limpiado desde el cliente');
        }

        // También enviar mensaje al service worker para limpiar el contador interno
        if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
            navigator.serviceWorker.controller.postMessage({
                type: 'CLEAR_BADGE'
            });
        }
    } catch (error) {
        console.error('[PWA] Error limpiando badge:', error);
    }
}

/**
 * Actualiza el badge a un número específico
 */
async function setNotificationBadge(count) {
    try {
        if ('setAppBadge' in navigator) {
            if (count > 0) {
                await navigator.setAppBadge(count);
                console.log('[PWA] Badge actualizado a:', count);
            } else {
                await navigator.clearAppBadge();
                console.log('[PWA] Badge limpiado');
            }
        }

        // También enviar mensaje al service worker
        if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
            navigator.serviceWorker.controller.postMessage({
                type: 'SET_BADGE',
                count: count
            });
        }
    } catch (error) {
        console.error('[PWA] Error actualizando badge:', error);
    }
}

/**
 * Limpiar badge cuando el usuario abre la app
 */
if (isPWAInstalled()) {
    window.addEventListener('focus', () => {
        // Cuando el usuario enfoca la app, limpiar el badge después de un delay
        // (para dar tiempo a que vean las notificaciones)
        setTimeout(() => {
            clearNotificationBadge();
        }, 2000); // 2 segundos
    });
}

/**
 * Obtiene el estado actual de los permisos de notificación
 */
function getNotificationStatus() {
    if (!('Notification' in window)) {
        return {
            supported: false,
            permission: 'not-supported',
            message: 'Las notificaciones no están soportadas en este navegador'
        };
    }

    if (!('PushManager' in window)) {
        return {
            supported: false,
            permission: 'not-supported',
            message: 'Las notificaciones push no están soportadas'
        };
    }

    const permission = Notification.permission;
    const messages = {
        'granted': 'Notificaciones activadas ✓',
        'denied': 'Notificaciones bloqueadas ✗',
        'default': 'Notificaciones pendientes de activar'
    };

    return {
        supported: true,
        permission: permission,
        message: messages[permission] || 'Estado desconocido',
        canRequest: permission === 'default'
    };
}

/**
 * Muestra un indicador visual del estado de las notificaciones
 */
function showNotificationStatusIndicator() {
    // Evitar duplicados
    if (document.getElementById('notification-status-indicator')) {
        return;
    }

    const status = getNotificationStatus();

    // No mostrar si no está soportado
    if (!status.supported) {
        return;
    }

    // Crear contenedor del indicador
    const indicator = document.createElement('div');
    indicator.id = 'notification-status-indicator';
    indicator.style.cssText = `
        position: fixed;
        top: 10px;
        right: 10px;
        background: ${status.permission === 'granted' ? '#28a745' : status.permission === 'denied' ? '#dc3545' : '#ffc107'};
        color: white;
        padding: 10px 15px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        z-index: 9999;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 14px;
        display: flex;
        align-items: center;
        gap: 10px;
        cursor: ${status.canRequest ? 'pointer' : 'default'};
        transition: all 0.3s ease;
    `;

    // Icono según el estado
    const icon = status.permission === 'granted' ? '🔔' :
                 status.permission === 'denied' ? '🔕' : '🔔';

    // Si están bloqueadas, mostrar botón de ayuda
    const helpButton = status.permission === 'denied' ?
        '<button id="help-notifications-btn" style="background: white; color: #dc3545; border: none; padding: 5px 12px; border-radius: 5px; font-weight: bold; margin-left: 5px; cursor: pointer;">¿Cómo activar?</button>' : '';

    indicator.innerHTML = `
        <span style="font-size: 18px;">${icon}</span>
        <span id="notification-status-text">${status.message}</span>
        ${status.canRequest ? '<button id="enable-notifications-btn" style="background: white; color: #333; border: none; padding: 5px 12px; border-radius: 5px; font-weight: bold; margin-left: 5px; cursor: pointer;">Activar</button>' : ''}
        ${helpButton}
        <button id="close-notification-indicator" style="background: transparent; border: none; color: white; font-size: 18px; cursor: pointer; padding: 0; margin-left: 5px;">&times;</button>
    `;

    document.body.appendChild(indicator);

    // Si se puede solicitar permisos, agregar evento al botón
    if (status.canRequest) {
        const enableBtn = document.getElementById('enable-notifications-btn');
        if (enableBtn) {
            enableBtn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const granted = await requestNotificationPermission();
                if (granted) {
                    updateNotificationStatusIndicator();
                }
            });
        }
    }

    // Si están bloqueadas, agregar evento al botón de ayuda
    if (status.permission === 'denied') {
        const helpBtn = document.getElementById('help-notifications-btn');
        if (helpBtn) {
            helpBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                showUnblockInstructions();
            });
        }
    }

    // Botón de cerrar
    const closeBtn = document.getElementById('close-notification-indicator');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            indicator.remove();
        });
    }

    // Auto-ocultar después de 10 segundos si está activado
    if (status.permission === 'granted') {
        setTimeout(() => {
            if (indicator && indicator.parentElement) {
                indicator.style.opacity = '0';
                setTimeout(() => indicator.remove(), 300);
            }
        }, 10000);
    }
}

/**
 * Actualiza el indicador de estado de notificaciones
 */
function updateNotificationStatusIndicator() {
    const indicator = document.getElementById('notification-status-indicator');
    if (indicator) {
        indicator.remove();
    }
    showNotificationStatusIndicator();
}

/**
 * Diagnóstico completo de notificaciones (para consola)
 */
async function diagnosticarNotificaciones() {
    console.group('🔍 DIAGNÓSTICO DE NOTIFICACIONES');

    // 1. Soporte del navegador
    console.log('1️⃣ Soporte del navegador:');
    console.log('   - Notification API:', 'Notification' in window ? '✓ Soportado' : '✗ No soportado');
    console.log('   - Push API:', 'PushManager' in window ? '✓ Soportado' : '✗ No soportado');
    console.log('   - Service Worker:', 'serviceWorker' in navigator ? '✓ Soportado' : '✗ No soportado');

    // 2. Permisos
    console.log('\n2️⃣ Estado de permisos:');
    if ('Notification' in window) {
        console.log('   - Notification.permission:', Notification.permission);
        const status = getNotificationStatus();
        console.log('   - Estado:', status.message);
    }

    // 3. Service Worker
    console.log('\n3️⃣ Service Worker:');
    if ('serviceWorker' in navigator) {
        const registration = await navigator.serviceWorker.getRegistration();
        if (registration) {
            console.log('   - Registrado:', '✓ Sí');
            console.log('   - Scope:', registration.scope);
            console.log('   - Estado:', registration.active ? 'Activo' : 'Inactivo');
        } else {
            console.log('   - Registrado:', '✗ No');
        }
    }

    // 4. Suscripción Push
    console.log('\n4️⃣ Suscripción Push:');
    if ('serviceWorker' in navigator && 'PushManager' in window) {
        try {
            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.getSubscription();

            if (subscription) {
                console.log('   - Suscrito:', '✓ Sí');
                console.log('   - Endpoint:', subscription.endpoint);
                console.log('   - Guardado en servidor:', localStorage.getItem('push_subscribed') === 'true' ? '✓' : '✗');
            } else {
                console.log('   - Suscrito:', '✗ No');
            }
        } catch (error) {
            console.log('   - Error verificando suscripción:', error.message);
        }
    }

    // 5. PWA instalada
    console.log('\n5️⃣ PWA:');
    console.log('   - Instalada:', isPWAInstalled() ? '✓ Sí (modo standalone)' : '✗ No (navegador)');
    console.log('   - localStorage pwa_installed:', localStorage.getItem('pwa_installed'));

    // 6. Datos del contexto
    console.log('\n6️⃣ Contexto:');
    const negocio_slug = window.location.pathname.split('/')[1] || 'N/A';
    const esAdmin = window.location.pathname.includes('/admin/');
    console.log('   - Negocio slug:', negocio_slug);
    console.log('   - Es admin:', esAdmin ? '✓ Sí' : '✗ No');

    // 7. Recomendaciones
    console.log('\n7️⃣ Recomendaciones:');
    const status = getNotificationStatus();
    if (!status.supported) {
        console.warn('   ⚠️ Este navegador no soporta notificaciones push');
    } else if (status.permission === 'denied') {
        console.warn('   ⚠️ Los permisos fueron denegados. El usuario debe habilitarlos manualmente desde la configuración del navegador');
    } else if (status.permission === 'default') {
        console.log('   💡 Llama a window.PWA.requestNotificationPermission() para solicitar permisos');
    } else if (status.permission === 'granted') {
        console.log('   ✓ Todo configurado correctamente');
    }

    console.groupEnd();
}

/**
 * Muestra instrucciones para desbloquear notificaciones
 */
function showUnblockInstructions() {
    // Eliminar modal existente si hay uno
    const existingModal = document.getElementById('unblock-instructions-modal');
    if (existingModal) {
        existingModal.remove();
    }

    // Crear overlay
    const overlay = document.createElement('div');
    overlay.id = 'unblock-instructions-modal';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
    `;

    // Crear modal
    const modal = document.createElement('div');
    modal.style.cssText = `
        background: white;
        border-radius: 12px;
        padding: 25px;
        max-width: 500px;
        width: 100%;
        max-height: 90vh;
        overflow-y: auto;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    `;

    modal.innerHTML = `
        <div style="margin-bottom: 20px;">
            <h3 style="margin: 0 0 10px 0; color: #333; font-size: 20px;">
                🔔 Cómo activar las notificaciones
            </h3>
            <p style="margin: 0; color: #666; font-size: 14px;">
                Las notificaciones están bloqueadas. Sigue estos pasos para activarlas:
            </p>
        </div>

        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
            <h4 style="margin: 0 0 10px 0; color: #667eea; font-size: 16px;">
                📱 Paso 1: Abrir configuración
            </h4>
            <ol style="margin: 0; padding-left: 20px; color: #555; font-size: 14px; line-height: 1.6;">
                <li>Toca el menú de Chrome (⋮) arriba a la derecha</li>
                <li>Selecciona <strong>"Configuración"</strong></li>
                <li>Ve a <strong>"Configuración del sitio"</strong></li>
            </ol>
        </div>

        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
            <h4 style="margin: 0 0 10px 0; color: #667eea; font-size: 16px;">
                🔓 Paso 2: Desbloquear
            </h4>
            <ol style="margin: 0; padding-left: 20px; color: #555; font-size: 14px; line-height: 1.6;">
                <li>Busca <strong>"Notificaciones"</strong></li>
                <li>Encuentra <strong>"faciladmin.app"</strong> en la lista</li>
                <li>Cámbialo de <strong>"Bloqueado"</strong> a <strong>"Permitir"</strong></li>
            </ol>
        </div>

        <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #28a745;">
            <p style="margin: 0; color: #2e7d32; font-size: 13px; line-height: 1.5;">
                💡 <strong>Atajo rápido:</strong> También puedes ir directamente a<br>
                <code style="background: rgba(0,0,0,0.1); padding: 2px 6px; border-radius: 3px; font-size: 12px;">chrome://settings/content/siteDetails?site=https://faciladmin.app</code>
            </p>
        </div>

        <div style="display: flex; gap: 10px;">
            <button id="retry-notifications-btn" style="flex: 1; background: #667eea; color: white; border: none; padding: 12px; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 15px;">
                🔄 Ya lo activé, reintentar
            </button>
            <button id="close-instructions-btn" style="background: #f0f0f0; color: #666; border: none; padding: 12px 20px; border-radius: 8px; cursor: pointer; font-size: 15px;">
                Cerrar
            </button>
        </div>

        <div style="margin-top: 15px; padding: 10px; background: #fff3cd; border-radius: 6px;">
            <p style="margin: 0; font-size: 12px; color: #856404; line-height: 1.4;">
                <strong>Nota:</strong> Si los permisos siguen bloqueados después de cambiar la configuración,
                desinstala la app y vuelve a instalarla desde el panel de admin.
            </p>
        </div>
    `;

    overlay.appendChild(modal);
    document.body.appendChild(overlay);

    // Evento para reintentar
    document.getElementById('retry-notifications-btn').addEventListener('click', async () => {
        overlay.remove();

        // Verificar el estado actual
        const newStatus = getNotificationStatus();

        if (newStatus.permission === 'granted') {
            // Si ya está concedido, intentar suscribirse
            await subscribeToPushNotifications();
            updateNotificationStatusIndicator();
            alert('✓ ¡Notificaciones activadas correctamente!');
        } else if (newStatus.permission === 'default') {
            // Si ahora está en default, solicitar permiso
            const granted = await requestNotificationPermission();
            if (granted) {
                updateNotificationStatusIndicator();
                alert('✓ ¡Notificaciones activadas correctamente!');
            }
        } else {
            // Sigue bloqueado
            alert('⚠️ Los permisos siguen bloqueados.\n\nAsegúrate de cambiar "faciladmin.app" a "Permitir" en la configuración de Chrome.');
        }
    });

    // Evento para cerrar
    document.getElementById('close-instructions-btn').addEventListener('click', () => {
        overlay.remove();
    });

    // Cerrar al hacer clic fuera del modal
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            overlay.remove();
        }
    });
}

/**
 * Mostrar indicador al cargar la página si es PWA instalada
 */
window.addEventListener('load', () => {
    // Solo mostrar si la PWA está instalada o si estamos en admin
    const esAdmin = window.location.pathname.includes('/admin/');

    if (isPWAInstalled() || esAdmin) {
        // Esperar un poco para que el DOM esté listo
        setTimeout(() => {
            showNotificationStatusIndicator();
        }, 1500);
    }
});

// Exportar funciones para uso global
window.PWA = {
    promptInstall,
    isPWAInstalled,
    requestNotificationPermission,
    subscribeToPushNotifications,
    hideInstallBanner,
    clearNotificationBadge,
    setNotificationBadge,
    getNotificationStatus,
    showNotificationStatusIndicator,
    diagnosticarNotificaciones
};
