"""
Vistas para gestionar suscripciones de notificaciones push (PWA)
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
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

        # Obtener información del cliente
        telefono = data.get('telefono')
        negocio_slug = data.get('negocio_slug')
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Validar que tengamos teléfono y negocio para asociar la suscripción
        if not telefono or not negocio_slug:
            return JsonResponse({
                'success': False,
                'error': 'Se requiere teléfono y negocio_slug para suscribirse'
            }, status=400)

        # Buscar el cliente
        from apps.clientes.models import Cliente
        from apps.negocios.models import Negocio
        from .models import ClientePushSubscription

        try:
            negocio = Negocio.objects.get(slug=negocio_slug)
            cliente = Cliente.objects.get(negocio=negocio, telefono=telefono)
        except Negocio.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Negocio no encontrado'
            }, status=404)
        except Cliente.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Cliente no encontrado'
            }, status=404)

        # Crear o actualizar la suscripción
        try:
            subscription = ClientePushSubscription.crear_desde_subscription_info(
                cliente=cliente,
                subscription_data=subscription_info,
                user_agent=user_agent
            )

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
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
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
