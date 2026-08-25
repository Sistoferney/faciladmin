"""
Script de prueba para verificar las vistas HTTP de notificaciones push
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.test import RequestFactory
from apps.notificaciones.push_views import subscribe_push, unsubscribe_push, get_vapid_public_key
from apps.clientes.models import Cliente
from apps.negocios.models import Negocio
from apps.notificaciones.models import ClientePushSubscription
import json


def test_get_vapid_public_key():
    """Prueba 1: Obtener clave pública VAPID"""
    print("\n" + "="*60)
    print("PRUEBA 1: GET /push/vapid-public-key/")
    print("="*60)

    try:
        factory = RequestFactory()
        request = factory.get('/push/vapid-public-key/')

        response = get_vapid_public_key(request)

        print(f"Status: {response.status_code}")
        data = json.loads(response.content)
        print(f"Response: {data}")

        if 'publicKey' in data:
            print(f"OK: Clave publica VAPID presente")
            return True
        else:
            print(f"ERROR: No se encontro publicKey en la respuesta")
            return False

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_subscribe_push():
    """Prueba 2: Suscribir a notificaciones push"""
    print("\n" + "="*60)
    print("PRUEBA 2: POST /push/subscribe/")
    print("="*60)

    try:
        # Obtener cliente y negocio de prueba
        cliente = Cliente.objects.first()
        negocio = cliente.negocio

        print(f"Cliente: {cliente.nombre} ({cliente.telefono})")
        print(f"Negocio: {negocio.nombre} ({negocio.slug})")

        # Preparar datos de suscripción
        payload = {
            'subscription': {
                'endpoint': 'https://fcm.googleapis.com/fcm/send/test-vista-endpoint',
                'keys': {
                    'auth': 'test-auth-vista-123',
                    'p256dh': 'test-p256dh-vista-456'
                }
            },
            'telefono': str(cliente.telefono),
            'negocio_slug': negocio.slug
        }

        factory = RequestFactory()
        request = factory.post(
            '/push/subscribe/',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response = subscribe_push(request)

        print(f"Status: {response.status_code}")
        data = json.loads(response.content)
        print(f"Response: {data}")

        if data.get('success'):
            print(f"OK: Suscripcion creada exitosamente")
            print(f"   - Subscription ID: {data.get('subscription_id')}")

            # Verificar que se creó en la base de datos
            subscription = ClientePushSubscription.objects.filter(
                endpoint=payload['subscription']['endpoint']
            ).first()

            if subscription:
                print(f"OK: Suscripcion encontrada en BD")
                print(f"   - Cliente: {subscription.cliente.nombre}")
                print(f"   - Activa: {subscription.activa}")

                # Limpiar
                subscription.delete()
                print(f"OK: Suscripcion eliminada para limpiar")

                return True
            else:
                print(f"ERROR: Suscripcion no encontrada en BD")
                return False
        else:
            print(f"ERROR: {data.get('error')}")
            return False

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_subscribe_push_sin_datos():
    """Prueba 3: Suscribir sin datos requeridos (debe fallar)"""
    print("\n" + "="*60)
    print("PRUEBA 3: POST /push/subscribe/ (sin telefono/negocio)")
    print("="*60)

    try:
        payload = {
            'subscription': {
                'endpoint': 'https://test.com',
                'keys': {'auth': 'auth', 'p256dh': 'p256dh'}
            }
            # Falta telefono y negocio_slug
        }

        factory = RequestFactory()
        request = factory.post(
            '/push/subscribe/',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response = subscribe_push(request)

        print(f"Status: {response.status_code}")
        data = json.loads(response.content)
        print(f"Response: {data}")

        if not data.get('success') and response.status_code == 400:
            print(f"OK: Vista retorna error 400 cuando faltan datos")
            return True
        else:
            print(f"ERROR: Deberia retornar error 400")
            return False

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_unsubscribe_push():
    """Prueba 4: Desuscribir de notificaciones push"""
    print("\n" + "="*60)
    print("PRUEBA 4: POST /push/unsubscribe/")
    print("="*60)

    try:
        # Crear una suscripción primero
        cliente = Cliente.objects.first()
        endpoint = 'https://fcm.googleapis.com/fcm/send/test-unsubscribe'

        subscription = ClientePushSubscription.crear_desde_subscription_info(
            cliente=cliente,
            subscription_data={
                'endpoint': endpoint,
                'keys': {'auth': 'auth-unsub', 'p256dh': 'p256dh-unsub'}
            }
        )

        print(f"Suscripcion creada: ID {subscription.id}")
        print(f"Activa antes de desuscribir: {subscription.activa}")

        # Desuscribir
        payload = {'endpoint': endpoint}

        factory = RequestFactory()
        request = factory.post(
            '/push/unsubscribe/',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response = unsubscribe_push(request)

        print(f"Status: {response.status_code}")
        data = json.loads(response.content)
        print(f"Response: {data}")

        if data.get('success'):
            print(f"OK: Desuscripcion exitosa")

            # Verificar que se desactivó
            subscription.refresh_from_db()
            print(f"Activa despues de desuscribir: {subscription.activa}")

            if not subscription.activa:
                print(f"OK: Suscripcion marcada como inactiva")

                # Limpiar
                subscription.delete()
                print(f"OK: Suscripcion eliminada para limpiar")

                return True
            else:
                print(f"ERROR: Suscripcion sigue activa")
                subscription.delete()
                return False
        else:
            print(f"ERROR: {data.get('error')}")
            subscription.delete()
            return False

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_unsubscribe_inexistente():
    """Prueba 5: Desuscribir endpoint que no existe (debe retornar 404)"""
    print("\n" + "="*60)
    print("PRUEBA 5: POST /push/unsubscribe/ (endpoint inexistente)")
    print("="*60)

    try:
        payload = {'endpoint': 'https://endpoint-que-no-existe.com'}

        factory = RequestFactory()
        request = factory.post(
            '/push/unsubscribe/',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response = unsubscribe_push(request)

        print(f"Status: {response.status_code}")
        data = json.loads(response.content)
        print(f"Response: {data}")

        if not data.get('success') and response.status_code == 404:
            print(f"OK: Vista retorna error 404 para endpoint inexistente")
            return True
        else:
            print(f"ERROR: Deberia retornar error 404")
            return False

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ejecutar todas las pruebas"""
    print("\n" + "="*60)
    print("INICIANDO PRUEBAS DE VISTAS HTTP")
    print("="*60)

    resultados = []

    # Ejecutar pruebas
    resultados.append(("GET vapid-public-key", test_get_vapid_public_key()))
    resultados.append(("POST subscribe (exitoso)", test_subscribe_push()))
    resultados.append(("POST subscribe (sin datos)", test_subscribe_push_sin_datos()))
    resultados.append(("POST unsubscribe (exitoso)", test_unsubscribe_push()))
    resultados.append(("POST unsubscribe (inexistente)", test_unsubscribe_inexistente()))

    # Resumen
    print("\n" + "="*60)
    print("RESUMEN DE PRUEBAS")
    print("="*60)

    for nombre, resultado in resultados:
        estado = "EXITOSA" if resultado else "FALLIDA"
        simbolo = "[OK]" if resultado else "[ERROR]"
        print(f"{simbolo} {nombre}: {estado}")

    exitosas = sum(1 for _, r in resultados if r)
    total = len(resultados)

    print(f"\nResultado final: {exitosas}/{total} pruebas exitosas")

    if exitosas == total:
        print("\nTODAS LAS PRUEBAS PASARON CORRECTAMENTE!")
        return 0
    else:
        print(f"\n{total - exitosas} PRUEBA(S) FALLARON")
        return 1


if __name__ == '__main__':
    exit(main())
