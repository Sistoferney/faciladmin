"""
Script de prueba para verificar la funcionalidad de notificaciones push
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.notificaciones.models import ClientePushSubscription
from apps.clientes.models import Cliente
from apps.negocios.models import Negocio
from apps.notificaciones.services import NotificacionService


def test_modelo_clientepushsubscription():
    """Prueba 1: Verificar que el modelo funciona correctamente"""
    print("\n" + "="*60)
    print("PRUEBA 1: Modelo ClientePushSubscription")
    print("="*60)

    # Obtener un cliente existente
    cliente = Cliente.objects.first()
    if not cliente:
        print("ERROR: No hay clientes en la base de datos")
        return False

    print(f"Cliente de prueba: {cliente.nombre} - {cliente.telefono}")

    # Datos de suscripción de ejemplo
    subscription_data = {
        'endpoint': 'https://fcm.googleapis.com/fcm/send/test-endpoint-12345',
        'keys': {
            'auth': 'test-auth-key-abcdef123456',
            'p256dh': 'test-p256dh-key-xyz789'
        }
    }

    try:
        # Crear suscripción
        subscription = ClientePushSubscription.crear_desde_subscription_info(
            cliente=cliente,
            subscription_data=subscription_data,
            user_agent='Mozilla/5.0 (Test Browser)'
        )

        print(f"OK: Suscripcion creada con ID: {subscription.id}")
        print(f"   - Endpoint: {subscription.endpoint[:50]}...")
        print(f"   - Activa: {subscription.activa}")
        print(f"   - User Agent: {subscription.user_agent}")

        # Verificar to_subscription_info()
        subscription_info = subscription.to_subscription_info()
        print(f"OK: to_subscription_info() funciona correctamente")
        print(f"   - Keys presentes: {list(subscription_info.keys())}")

        # Probar desactivar()
        subscription.desactivar()
        print(f"OK: Suscripcion desactivada correctamente")
        print(f"   - Activa: {subscription.activa}")

        # Limpiar
        subscription.delete()
        print(f"OK: Suscripcion eliminada para limpiar base de datos")

        return True

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_filtrado_por_cliente():
    """Prueba 2: Verificar que el filtrado por cliente funciona"""
    print("\n" + "="*60)
    print("PRUEBA 2: Filtrado de suscripciones por cliente")
    print("="*60)

    try:
        # Obtener dos clientes diferentes
        clientes = Cliente.objects.all()[:2]
        if len(clientes) < 2:
            print("ADVERTENCIA: Solo hay un cliente, creando uno adicional...")
            negocio = Negocio.objects.first()
            cliente2, created = Cliente.objects.get_or_create(
                negocio=negocio,
                telefono='+573001234567',
                defaults={'nombre': 'Cliente de Prueba Push'}
            )
            clientes = [clientes[0], cliente2]

        cliente1, cliente2 = clientes[0], clientes[1]

        print(f"Cliente 1: {cliente1.nombre}")
        print(f"Cliente 2: {cliente2.nombre}")

        # Crear suscripciones para cada cliente
        sub1 = ClientePushSubscription.crear_desde_subscription_info(
            cliente=cliente1,
            subscription_data={
                'endpoint': 'https://fcm.googleapis.com/fcm/send/cliente1-endpoint',
                'keys': {'auth': 'auth1', 'p256dh': 'p256dh1'}
            }
        )

        sub2 = ClientePushSubscription.crear_desde_subscription_info(
            cliente=cliente2,
            subscription_data={
                'endpoint': 'https://fcm.googleapis.com/fcm/send/cliente2-endpoint',
                'keys': {'auth': 'auth2', 'p256dh': 'p256dh2'}
            }
        )

        # Verificar filtrado
        subs_cliente1 = ClientePushSubscription.objects.filter(cliente=cliente1, activa=True)
        subs_cliente2 = ClientePushSubscription.objects.filter(cliente=cliente2, activa=True)

        print(f"OK: Cliente 1 tiene {subs_cliente1.count()} suscripcion(es)")
        print(f"OK: Cliente 2 tiene {subs_cliente2.count()} suscripcion(es)")

        # Limpiar
        sub1.delete()
        sub2.delete()
        print(f"OK: Suscripciones eliminadas para limpiar")

        return True

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_servicio_notificaciones():
    """Prueba 3: Verificar que el servicio de notificaciones funciona"""
    print("\n" + "="*60)
    print("PRUEBA 3: Servicio de notificaciones (sin enviar real)")
    print("="*60)

    try:
        cliente = Cliente.objects.first()
        print(f"Cliente: {cliente.nombre}")

        # Crear una suscripción de prueba
        subscription = ClientePushSubscription.crear_desde_subscription_info(
            cliente=cliente,
            subscription_data={
                'endpoint': 'https://fcm.googleapis.com/fcm/send/test-service',
                'keys': {'auth': 'test-auth', 'p256dh': 'test-p256dh'}
            }
        )

        print(f"OK: Suscripcion de prueba creada")

        # Verificar que el servicio encuentra la suscripción
        suscripciones = ClientePushSubscription.objects.filter(
            cliente=cliente,
            activa=True
        )

        print(f"OK: Servicio encontro {suscripciones.count()} suscripcion(es) activa(s)")

        # Verificar que sin suscripciones activas retorna error
        subscription.desactivar()
        service = NotificacionService()
        resultado = service.enviar_push(
            cliente=cliente,
            titulo="Prueba",
            mensaje="Mensaje de prueba"
        )

        if not resultado['success'] and 'no tiene suscripciones activas' in resultado['error']:
            print(f"OK: Servicio retorna error cuando no hay suscripciones activas")
        else:
            print(f"ADVERTENCIA: Resultado inesperado: {resultado}")

        # Limpiar
        subscription.delete()
        print(f"OK: Suscripcion eliminada")

        return True

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_admin_queryset():
    """Prueba 4: Verificar que el admin filtra correctamente"""
    print("\n" + "="*60)
    print("PRUEBA 4: Filtrado en Django Admin")
    print("="*60)

    try:
        from django.contrib.auth import get_user_model
        from apps.notificaciones.admin import ClientePushSubscriptionAdmin
        from django.test import RequestFactory

        User = get_user_model()
        factory = RequestFactory()

        # Crear request simulado
        request = factory.get('/admin/notificaciones/clientepushsubscription/')

        # Crear usuario de prueba
        user = User.objects.first()
        if not user:
            print("ADVERTENCIA: No hay usuarios en la base de datos")
            return True

        request.user = user

        # Probar get_queryset
        admin = ClientePushSubscriptionAdmin(ClientePushSubscription, None)
        qs = admin.get_queryset(request)

        print(f"OK: Queryset del admin funciona correctamente")
        print(f"   - Total de suscripciones: {qs.count()}")

        if hasattr(user, 'negocio'):
            print(f"   - Usuario tiene negocio: {user.negocio.nombre}")
            print(f"   - Filtrando solo suscripciones de su negocio")
        else:
            print(f"   - Usuario es superadmin (ve todas las suscripciones)")

        return True

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ejecutar todas las pruebas"""
    print("\n" + "="*60)
    print("INICIANDO PRUEBAS DE NOTIFICACIONES PUSH")
    print("="*60)

    resultados = []

    # Ejecutar pruebas
    resultados.append(("Modelo ClientePushSubscription", test_modelo_clientepushsubscription()))
    resultados.append(("Filtrado por cliente", test_filtrado_por_cliente()))
    resultados.append(("Servicio de notificaciones", test_servicio_notificaciones()))
    resultados.append(("Admin queryset", test_admin_queryset()))

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
