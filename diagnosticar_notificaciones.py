#!/usr/bin/env python
"""
Script de diagnóstico para notificaciones push
Ejecutar con: python diagnosticar_notificaciones.py
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.notificaciones.models import ClientePushSubscription, UsuarioPushSubscription
from apps.negocios.models import Negocio
from apps.notificaciones.services import NotificacionService
from django.conf import settings

def diagnosticar():
    print("=" * 80)
    print("DIAGNOSTICO DE NOTIFICACIONES PUSH")
    print("=" * 80)

    # 1. Verificar configuración VAPID
    print("\n[1] Configuracion VAPID:")
    vapid_public = settings.WEBPUSH_SETTINGS.get('VAPID_PUBLIC_KEY', '')
    vapid_private = settings.WEBPUSH_SETTINGS.get('VAPID_PRIVATE_KEY', '')
    vapid_email = settings.WEBPUSH_SETTINGS.get('VAPID_ADMIN_EMAIL', '')

    print(f"   - Clave publica: {'OK Configurada' if vapid_public else 'X NO configurada'}")
    print(f"   - Clave privada: {'OK Configurada' if vapid_private else 'X NO configurada'}")
    print(f"   - Email admin: {vapid_email or 'X NO configurado'}")

    # 2. Suscripciones de clientes
    print("\n[2] Suscripciones de Clientes:")
    subs_clientes = ClientePushSubscription.objects.all()
    subs_clientes_activas = subs_clientes.filter(activa=True)
    print(f"   - Total: {subs_clientes.count()}")
    print(f"   - Activas: {subs_clientes_activas.count()}")

    if subs_clientes_activas.exists():
        print("\n   Últimas 5 suscripciones activas:")
        for sub in subs_clientes_activas.order_by('-created_at')[:5]:
            print(f"     - Cliente: {sub.cliente.nombre} ({sub.cliente.telefono})")
            print(f"       Negocio: {sub.cliente.negocio.nombre}")
            print(f"       Fecha: {sub.created_at.strftime('%Y-%m-%d %H:%M')}")

    # 3. Suscripciones de administradores
    print("\n[3] Suscripciones de Administradores:")
    subs_admin = UsuarioPushSubscription.objects.all()
    subs_admin_activas = subs_admin.filter(activa=True)
    print(f"   - Total: {subs_admin.count()}")
    print(f"   - Activas: {subs_admin_activas.count()}")

    if subs_admin_activas.exists():
        print("\n   Suscripciones activas de admin:")
        for sub in subs_admin_activas.order_by('-created_at'):
            print(f"     - Usuario: {sub.user.nombre} ({sub.user.email})")
            print(f"       Negocio: {sub.negocio.nombre}")
            print(f"       Fecha: {sub.created_at.strftime('%Y-%m-%d %H:%M')}")
            print(f"       Endpoint: {sub.endpoint[:50]}...")
    else:
        print("   ! NO HAY SUSCRIPCIONES DE ADMIN ACTIVAS")

    # 4. Negocios
    print("\n[4] Negocios registrados:")
    negocios = Negocio.objects.all()
    print(f"   - Total: {negocios.count()}")

    for negocio in negocios:
        subs_negocio = UsuarioPushSubscription.objects.filter(negocio=negocio, activa=True).count()
        print(f"     - {negocio.nombre} ({negocio.slug})")
        print(f"       Admin: {negocio.administrador.nombre}")
        print(f"       Suscripciones admin activas: {subs_negocio}")

    # 5. Prueba de envío (solo si hay suscripciones activas de admin)
    print("\n[5] Prueba de envío:")

    if not vapid_public or not vapid_private:
        print("   X No se puede probar: VAPID no configurado")
        return

    if not subs_admin_activas.exists():
        print("   ! No se puede probar: No hay suscripciones de admin activas")
        print("\n   > Solucion:")
        print("      1. Abre la PWA instalada en tu dispositivo")
        print("      2. Ve al panel de admin")
        print("      3. Acepta los permisos de notificacion")
        print("      4. Ejecuta este script nuevamente")
        return

    # Intentar enviar notificación de prueba
    print("   Intentando enviar notificacion de prueba...")

    # Usar la primera suscripción activa de admin
    sub_prueba = subs_admin_activas.first()
    print(f"   Enviando a: {sub_prueba.user.nombre} ({sub_prueba.negocio.nombre})")

    try:
        from pywebpush import webpush
        import json

        payload = {
            'head': 'TEST Prueba de notificacion',
            'body': 'Esta es una notificacion de prueba del sistema FacilAdmin',
            'icon': '/static/images/faciladmin-logo.png',
            'url': f'/{sub_prueba.negocio.slug}/admin/',
            'tag': 'test-notification',
            'requireInteraction': False,
            'vibrate': [200, 100, 200]
        }

        subscription_info = sub_prueba.to_subscription_info()

        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload),
            vapid_private_key=vapid_private,
            vapid_claims={
                'sub': f"mailto:{vapid_email}"
            }
        )

        print("   OK Notificacion enviada exitosamente!")
        print("\n   * Revisa tu dispositivo, deberias recibir la notificacion.")

    except Exception as e:
        print(f"   X Error al enviar notificación: {e}")
        print(f"\n   Detalles del error:")
        import traceback
        print(traceback.format_exc())

    print("\n" + "=" * 80)

if __name__ == '__main__':
    diagnosticar()
