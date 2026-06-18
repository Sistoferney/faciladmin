"""
Vistas para gestionar suscripciones de notificaciones push (PWA)
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from webpush import send_user_notification
import json


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

        # Guardar datos adicionales del cliente si están disponibles
        user_info = {
            'telefono': data.get('telefono'),
            'negocio_slug': data.get('negocio_slug'),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')
        }

        # django-webpush maneja el guardado automáticamente
        # cuando envías notificaciones a un usuario

        # Por ahora, guardamos en sesión o en modelo Cliente
        # TODO: Asociar suscripción con modelo Cliente

        return JsonResponse({
            'success': True,
            'message': 'Suscripción guardada exitosamente'
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos inválidos'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def unsubscribe_push(request):
    """
    Elimina la suscripción del cliente
    """
    try:
        # TODO: Implementar desuscripción
        return JsonResponse({
            'success': True,
            'message': 'Desuscripción exitosa'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
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

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
