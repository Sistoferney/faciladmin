"""
Vistas para gestionar suscripciones de notificaciones push (PWA)
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)


def _desactivar_endpoints_anteriores(data, endpoint_actual):
    """
    Desactiva las suscripciones que este mismo dispositivo canceló al renovar la
    suya (migración del Service Worker o clave VAPID vieja), en las dos tablas:
    el Service Worker antiguo compartía la suscripción entre panel y mini-página.
    Los endpoints son secretos que solo conoce el dispositivo que los creó.
    """
    from .models import ClientePushSubscription, UsuarioPushSubscription

    anteriores = data.get('endpoints_anteriores') or []
    if not isinstance(anteriores, list):
        return 0
    anteriores = [e for e in anteriores[:5] if isinstance(e, str) and e and e != endpoint_actual]
    if not anteriores:
        return 0
    total = 0
    for modelo in (UsuarioPushSubscription, ClientePushSubscription):
        total += modelo.objects.filter(endpoint__in=anteriores, activa=True).update(activa=False)
    if total:
        logger.info('Desactivadas %s suscripciones anteriores del mismo dispositivo', total)
    return total


def _separar_de_la_otra_app(data, suscripcion):
    """
    Una suscripción push pertenece a un solo Service Worker, es decir, a una
    sola app: el panel del dueño o la mini-página del cliente.

    Un error del navegador (ver obtenerRegistro en pwa-register.js) hacía que
    el panel se suscribiera con el Service Worker de la mini-página del mismo
    celular: los avisos del dueño llegaban a la app del cliente. Al guardar:
    - Se desactiva el mismo endpoint en la tabla de la otra app.
    - Se desactivan en esta tabla los endpoints que el navegador reporta como
      de la otra app (endpoints_otra_app).
    """
    from .models import ClientePushSubscription, UsuarioPushSubscription

    es_dueno = isinstance(suscripcion, UsuarioPushSubscription)
    propia, otra = (
        (UsuarioPushSubscription, ClientePushSubscription) if es_dueno
        else (ClientePushSubscription, UsuarioPushSubscription)
    )
    total = otra.objects.filter(endpoint=suscripcion.endpoint, activa=True).update(activa=False)

    ajenos = data.get('endpoints_otra_app') or []
    if isinstance(ajenos, list):
        ajenos = [e for e in ajenos[:5] if isinstance(e, str) and e and e != suscripcion.endpoint]
        if ajenos:
            total += propia.objects.filter(endpoint__in=ajenos, activa=True).update(activa=False)
    if total:
        logger.info('Desactivadas %s suscripciones cruzadas entre panel y mini-página', total)
    return total


@require_http_methods(["GET"])
def get_vapid_public_key(request):
    """
    Retorna la clave pública VAPID para que el cliente se suscriba
    """
    return JsonResponse({
        'publicKey': settings.WEBPUSH_SETTINGS.get('VAPID_PUBLIC_KEY', '')
    })


@csrf_exempt
@require_http_methods(["POST"])
def subscribe_push(request):
    """
    Guarda la suscripción del cliente a notificaciones push
    """
    try:
        data = json.loads(request.body)
        subscription_info = data.get('subscription')

        if not subscription_info:
            return JsonResponse({
                'success': False,
                'error': 'No se recibió información de suscripción'
            }, status=400)

        negocio_slug = data.get('negocio_slug')
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        if not negocio_slug:
            return JsonResponse({
                'success': False,
                'error': 'Se requiere negocio_slug para suscribirse'
            }, status=400)

        from apps.negocios.models import Negocio
        from apps.negocios.public_views import _cliente_verificado
        from .models import ClientePushSubscription

        try:
            negocio = Negocio.objects.get(slug=negocio_slug)
        except Negocio.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Negocio no encontrado'
            }, status=404)

        # El cliente se toma de la sesión (se identificó al agendar o en
        # "Mis citas"), no de un teléfono enviado por el navegador: así nadie
        # puede suscribirse a las notificaciones de otra persona.
        # En iPhone la app instalada no comparte almacenamiento con Safari,
        # por eso el cliente debe identificarse una vez dentro de la app.
        cliente = _cliente_verificado(request, negocio)
        if not cliente:
            return JsonResponse({
                'success': False,
                'codigo': 'identificacion_requerida',
                'error': 'Ingresa tu teléfono en "Mis citas" para activar las notificaciones'
            }, status=403)

        # Crear o actualizar la suscripción
        try:
            subscription = ClientePushSubscription.crear_desde_subscription_info(
                cliente=cliente,
                subscription_data=subscription_info,
                user_agent=user_agent
            )
            _desactivar_endpoints_anteriores(data, subscription.endpoint)
            _separar_de_la_otra_app(data, subscription)

            return JsonResponse({
                'success': True,
                'message': 'Suscripción guardada exitosamente',
                'subscription_id': subscription.id
            })

        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos inválidos'
        }, status=400)
    except Exception:
        logger.exception('Error en %s', request.path)
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def unsubscribe_push(request):
    """
    Elimina (desactiva) la suscripción del cliente
    """
    try:
        data = json.loads(request.body)
        endpoint = data.get('endpoint')

        if not endpoint:
            return JsonResponse({
                'success': False,
                'error': 'Se requiere el endpoint de la suscripción'
            }, status=400)

        from .models import ClientePushSubscription

        # Buscar la suscripción por endpoint y desactivarla
        try:
            subscription = ClientePushSubscription.objects.get(endpoint=endpoint)
            subscription.desactivar()

            return JsonResponse({
                'success': True,
                'message': 'Desuscripción exitosa'
            })

        except ClientePushSubscription.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Suscripción no encontrada'
            }, status=404)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos inválidos'
        }, status=400)
    except Exception:
        logger.exception('Error en %s', request.path)
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def subscribe_admin_push(request):
    """
    Guarda la suscripción del usuario administrador/dueño de negocio

    IMPORTANTE: Requiere autenticación obligatoria para prevenir que
    usuarios no autorizados reciban notificaciones privadas de clientes.
    """
    try:
        # VALIDACIÓN DE SEGURIDAD: Usuario debe estar autenticado
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Autenticación requerida'
            }, status=401)

        data = json.loads(request.body)
        subscription_info = data.get('subscription')
        negocio_slug = data.get('negocio_slug')

        if not subscription_info:
            return JsonResponse({
                'success': False,
                'error': 'No se recibió información de suscripción'
            }, status=400)

        user_agent = request.META.get('HTTP_USER_AGENT', '')

        from apps.negocios.models import Negocio
        from .models import UsuarioPushSubscription

        negocio = None
        user = request.user

        # Opción 1: Negocio identificado por slug
        if negocio_slug:
            try:
                negocio = Negocio.objects.get(slug=negocio_slug)

                # VALIDACIÓN DE SEGURIDAD: Verificar que el usuario sea el admin del negocio
                if negocio.administrador != request.user:
                    return JsonResponse({
                        'success': False,
                        'error': 'No tienes permisos para suscribirte a este negocio'
                    }, status=403)

            except Negocio.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'Negocio no encontrado: {negocio_slug}'
                }, status=404)

        # Opción 2: Buscar negocio del usuario autenticado
        else:
            try:
                if hasattr(request.user, 'negocio'):
                    negocio = request.user.negocio
                else:
                    # Buscar si es administrador de algún negocio
                    negocio = Negocio.objects.filter(administrador=request.user).first()

                if not negocio:
                    return JsonResponse({
                        'success': False,
                        'error': 'Usuario no tiene negocio asociado'
                    }, status=404)
            except Exception:
                logger.exception('Error buscando negocio del usuario %s', request.user.pk)
                return JsonResponse({
                    'success': False,
                    'error': 'Error interno del servidor'
                }, status=500)

        # Crear o actualizar la suscripción
        try:
            subscription = UsuarioPushSubscription.crear_desde_subscription_info(
                user=user,
                negocio=negocio,
                subscription_data=subscription_info,
                user_agent=user_agent
            )
            _desactivar_endpoints_anteriores(data, subscription.endpoint)
            _separar_de_la_otra_app(data, subscription)

            return JsonResponse({
                'success': True,
                'message': 'Suscripción de administrador guardada exitosamente',
                'subscription_id': subscription.id,
                'negocio': negocio.nombre
            })

        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos inválidos'
        }, status=400)
    except Exception:
        logger.exception('Error en %s', request.path)
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def test_push_notification(request):
    """
    Envía una notificación de prueba (solo para desarrollo)
    """
    if not settings.DEBUG:
        return JsonResponse({
            'success': False,
            'error': 'Solo disponible en modo debug'
        }, status=403)

    try:
        payload = {
            'head': '¡Notificación de prueba!',
            'body': 'Si ves esto, las notificaciones push están funcionando correctamente.',
            'icon': '/static/images/faciladmin-logo.png',
            'url': '/'
        }

        # TODO: Enviar a usuario específico cuando tengamos autenticación

        return JsonResponse({
            'success': True,
            'message': 'Notificación de prueba enviada'
        })

    except Exception:
        logger.exception('Error en %s', request.path)
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=500)
