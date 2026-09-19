"""
Diagnóstico completo del flujo de notificaciones push al admin
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from apps.notificaciones.models import UsuarioPushSubscription, ClientePushSubscription
from apps.negocios.models import Negocio
from apps.citas.models import Cita
from apps.clientes.models import Cliente
from django.contrib.auth import get_user_model
from django.conf import settings
import json

User = get_user_model()

def diagnosticar():
    print("\n" + "="*60)
    print("DIAGNOSTICO DE NOTIFICACIONES PUSH AL ADMIN")
    print("="*60)

    # 1. Verificar configuración VAPID
    print("\n1. CONFIGURACION VAPID:")
    vapid_public = settings.WEBPUSH_SETTINGS.get('VAPID_PUBLIC_KEY', '')
    vapid_private = settings.WEBPUSH_SETTINGS.get('VAPID_PRIVATE_KEY', '')
    vapid_email = settings.WEBPUSH_SETTINGS.get('VAPID_ADMIN_EMAIL', '')

    print(f"   - VAPID_PUBLIC_KEY: {'Configurada' if vapid_public else 'NO configurada'} ({len(vapid_public)} chars)")
    print(f"   - VAPID_PRIVATE_KEY: {'Configurada' if vapid_private else 'NO configurada'} ({len(vapid_private)} chars)")
    print(f"   - VAPID_ADMIN_EMAIL: {vapid_email if vapid_email else 'NO configurado'}")

    # 2. Verificar negocios
    print("\n2. NEGOCIOS:")
    negocios = Negocio.objects.all()
    print(f"   - Total negocios: {negocios.count()}")

    for negocio in negocios:
        print(f"\n   Negocio: {negocio.nombre} (slug: {negocio.slug})")
        print(f"   - Administrador: {negocio.administrador.username if negocio.administrador else 'Sin admin'}")
        print(f"   - Administrador ID: {negocio.administrador.id if negocio.administrador else 'N/A'}")

        # Verificar suscripciones de este negocio
        subs_admin = UsuarioPushSubscription.objects.filter(negocio=negocio)
        print(f"   - Suscripciones admin totales: {subs_admin.count()}")
        subs_admin_activas = subs_admin.filter(activa=True)
        print(f"   - Suscripciones admin ACTIVAS: {subs_admin_activas.count()}")

        for sub in subs_admin_activas:
            print(f"      * ID: {sub.id}")
            print(f"        User: {sub.user.username}")
            print(f"        Endpoint: {sub.endpoint[:60]}...")
            print(f"        Creada: {sub.fecha_creacion}")

    # 3. Verificar suscripciones de usuarios
    print("\n3. SUSCRIPCIONES DE ADMIN (todos los usuarios):")
    total_admin_subs = UsuarioPushSubscription.objects.all()
    print(f"   - Total suscripciones de admin: {total_admin_subs.count()}")
    activas_admin = total_admin_subs.filter(activa=True)
    print(f"   - Suscripciones ACTIVAS: {activas_admin.count()}")

    # 4. Verificar citas recientes
    print("\n4. CITAS RECIENTES:")
    citas_recientes = Cita.objects.all().order_by('-fecha_creacion')[:5]
    print(f"   - Total citas: {Cita.objects.count()}")
    print(f"   - Ultimas 5 citas:")

    for cita in citas_recientes:
        print(f"\n      Cita ID: {cita.id}")
        print(f"      - Cliente: {cita.cliente.nombre} ({cita.cliente.telefono})")
        print(f"      - Negocio: {cita.negocio.nombre}")
        print(f"      - Servicio: {cita.servicio.nombre}")
        print(f"      - Fecha cita: {cita.fecha_hora}")
        print(f"      - Fecha creacion: {cita.fecha_creacion}")

    # 5. Verificar Celery
    print("\n5. CONFIGURACION CELERY:")
    print(f"   - CELERY_TASK_ALWAYS_EAGER: {getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False)}")
    print(f"   - CELERY_BROKER_URL: {getattr(settings, 'CELERY_BROKER_URL', 'No configurado')}")

    # 6. Prueba de envío manual
    print("\n6. PRUEBA DE ENVIO MANUAL:")
    if activas_admin.exists():
        print(f"   - Hay {activas_admin.count()} suscripciones activas")
        print("   - Intentando enviar notificación de prueba...")

        try:
            from apps.notificaciones.services import NotificacionService
            from pywebpush import webpush

            service = NotificacionService()
            sub_prueba = activas_admin.first()

            print(f"   - Enviando a suscripción ID: {sub_prueba.id}")
            print(f"   - Usuario: {sub_prueba.user.username}")
            print(f"   - Negocio: {sub_prueba.negocio.nombre}")

            # Payload de prueba
            payload = {
                'head': 'Prueba de Notificacion',
                'body': 'Esta es una notificacion de prueba del sistema',
                'icon': '/static/images/faciladmin-logo.png',
                'url': f'/{sub_prueba.negocio.slug}/admin/',
                'tag': 'test-notification',
                'requireInteraction': True,
                'vibrate': [200, 100, 200]
            }

            subscription_info = sub_prueba.to_subscription_info()

            print(f"   - Subscription info: {json.dumps(subscription_info, indent=4)[:200]}...")

            # Intentar enviar
            resultado = webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=vapid_private,
                vapid_claims={
                    'sub': f"mailto:{vapid_email}"
                }
            )

            print(f"   - RESULTADO: SUCCESS!")
            print(f"   - Response: {resultado}")

        except Exception as e:
            print(f"   - ERROR: {type(e).__name__}: {str(e)}")
            import traceback
            print(f"\n   - Traceback:")
            traceback.print_exc()
    else:
        print("   - NO hay suscripciones activas para probar")

    print("\n" + "="*60)
    print("DIAGNOSTICO COMPLETADO")
    print("="*60 + "\n")

if __name__ == '__main__':
    diagnosticar()
