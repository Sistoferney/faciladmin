"""
Script de diagnóstico para notificaciones push
Ejecutar con: python manage.py shell < test_push_diagnostico.py
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.notificaciones.models import ClientePushSubscription, UsuarioPushSubscription
from apps.clientes.models import Cliente
from apps.negocios.models import Negocio
from apps.notificaciones.services import NotificacionService
from django.conf import settings

print("=" * 80)
print("DIAGNOSTICO DE NOTIFICACIONES PUSH")
print("=" * 80)

# 1. Verificar VAPID keys
print("\n1. VERIFICAR VAPID KEYS")
print("-" * 80)
vapid_public = settings.WEBPUSH_SETTINGS.get('VAPID_PUBLIC_KEY', '')
vapid_private = settings.WEBPUSH_SETTINGS.get('VAPID_PRIVATE_KEY', '')
vapid_email = settings.WEBPUSH_SETTINGS.get('VAPID_ADMIN_EMAIL', '')

print(f"VAPID_PUBLIC_KEY: {vapid_public[:50]}..." if vapid_public else "NO CONFIGURADA")
print(f"VAPID_PRIVATE_KEY: {vapid_private[:50]}..." if vapid_private else "NO CONFIGURADA")
print(f"VAPID_ADMIN_EMAIL: {vapid_email}")

if not vapid_public or not vapid_private:
    print("\n[ERROR] Las claves VAPID no estan configuradas correctamente!")
    print("Ejecuta este codigo para generar nuevas claves:")
    print("\nfrom py_vapid import Vapid01")
    print("vapid = Vapid01()")
    print("vapid.generate_keys()")
    print("print('VAPID_PRIVATE_KEY:', vapid.private_key.decode('utf-8'))")
    print("print('VAPID_PUBLIC_KEY:', vapid.public_key.decode('utf-8'))")
else:
    print("\n[OK] Claves VAPID configuradas correctamente")

# 2. Verificar suscripciones de clientes
print("\n2. SUSCRIPCIONES DE CLIENTES")
print("-" * 80)
total_clientes = ClientePushSubscription.objects.count()
activas_clientes = ClientePushSubscription.objects.filter(activa=True).count()
print(f"Total suscripciones de clientes: {total_clientes}")
print(f"Suscripciones activas: {activas_clientes}")

if activas_clientes > 0:
    print("\nPrimeras 5 suscripciones activas:")
    for sub in ClientePushSubscription.objects.filter(activa=True)[:5]:
        print(f"  - Cliente: {sub.cliente.nombre} ({sub.cliente.telefono})")
        print(f"    Negocio: {sub.cliente.negocio.nombre}")
        print(f"    Endpoint: {sub.endpoint[:50]}...")
        print(f"    Creada: {sub.fecha_creacion}")
        print()
else:
    print("\n[ADVERTENCIA] No hay suscripciones activas de clientes!")
    print("Esto significa que ningun cliente se ha suscrito a notificaciones push.")

# 3. Verificar suscripciones de administradores
print("\n3. SUSCRIPCIONES DE ADMINISTRADORES")
print("-" * 80)
total_admins = UsuarioPushSubscription.objects.count()
activas_admins = UsuarioPushSubscription.objects.filter(activa=True).count()
print(f"Total suscripciones de admins: {total_admins}")
print(f"Suscripciones activas: {activas_admins}")

if activas_admins > 0:
    print("\nPrimeras 5 suscripciones activas de admins:")
    for sub in UsuarioPushSubscription.objects.filter(activa=True)[:5]:
        print(f"  - Usuario: {sub.user.email}")
        print(f"    Negocio: {sub.negocio.nombre}")
        print(f"    Endpoint: {sub.endpoint[:50]}...")
        print(f"    Creada: {sub.fecha_creacion}")
        print()
else:
    print("\n[ADVERTENCIA] No hay suscripciones activas de administradores!")

# 4. Verificar clientes disponibles para prueba
print("\n4. CLIENTES DISPONIBLES PARA PRUEBA")
print("-" * 80)
total_clientes = Cliente.objects.count()
print(f"Total clientes en la base de datos: {total_clientes}")

if total_clientes > 0:
    print("\nPrimeros 5 clientes:")
    for cliente in Cliente.objects.all()[:5]:
        print(f"  - {cliente.nombre} ({cliente.telefono})")
        print(f"    Negocio: {cliente.negocio.nombre}")
        # Verificar si tiene suscripciones
        subs = ClientePushSubscription.objects.filter(cliente=cliente, activa=True).count()
        if subs > 0:
            print(f"    [OK] Tiene {subs} suscripcion(es) activa(s)")
        else:
            print(f"    [!] No tiene suscripciones activas")
        print()
else:
    print("\n[ADVERTENCIA] No hay clientes en la base de datos!")

# 5. Verificar negocios
print("\n5. NEGOCIOS REGISTRADOS")
print("-" * 80)
total_negocios = Negocio.objects.count()
print(f"Total negocios: {total_negocios}")

if total_negocios > 0:
    print("\nPrimeros 3 negocios:")
    for negocio in Negocio.objects.all()[:3]:
        print(f"  - {negocio.nombre} (slug: {negocio.slug})")
        clientes_count = Cliente.objects.filter(negocio=negocio).count()
        print(f"    Clientes: {clientes_count}")
        print()

# 6. Prueba de envío (solo si hay suscripciones)
print("\n6. PRUEBA DE ENVIO")
print("-" * 80)

if activas_clientes > 0:
    print("Se encontraron suscripciones activas. ¿Deseas enviar una notificacion de prueba?")
    print("\nPara enviar una prueba, ejecuta este codigo en el shell de Django:")
    print("\nfrom apps.notificaciones.services import NotificacionService")
    print("from apps.clientes.models import Cliente")
    print("\ncliente = Cliente.objects.first()")
    print("service = NotificacionService()")
    print("result = service.enviar_push(")
    print("    cliente=cliente,")
    print("    titulo='Prueba de notificacion',")
    print("    mensaje='Si ves esto, las notificaciones push funcionan correctamente!'")
    print(")")
    print("print('Resultado:', result)")
else:
    print("[!] No se puede enviar prueba: No hay suscripciones activas")
    print("\nPara que las notificaciones funcionen, los usuarios deben:")
    print("1. Instalar la PWA")
    print("2. Dar permiso de notificaciones")
    print("3. La suscripcion debe guardarse en el servidor")

# 7. Checklist final
print("\n7. CHECKLIST DE VERIFICACION")
print("-" * 80)
checks = []

# Check VAPID keys
checks.append(("VAPID keys configuradas", bool(vapid_public and vapid_private)))

# Check pywebpush instalado
try:
    import pywebpush
    checks.append(("pywebpush instalado", True))
except ImportError:
    checks.append(("pywebpush instalado", False))

# Check suscripciones
checks.append(("Hay suscripciones activas", activas_clientes > 0 or activas_admins > 0))

# Check clientes
checks.append(("Hay clientes en la BD", total_clientes > 0))

# Check service worker endpoint
try:
    from apps.core import views
    checks.append(("Service worker view existe", hasattr(views, 'service_worker')))
except:
    checks.append(("Service worker view existe", False))

for check_name, check_result in checks:
    status = "[OK]" if check_result else "[FALLO]"
    print(f"{status} {check_name}")

# Resumen
print("\n" + "=" * 80)
print("RESUMEN")
print("=" * 80)

fallos = sum(1 for _, result in checks if not result)
if fallos == 0:
    print("[OK] Todos los checks pasaron! El sistema esta configurado correctamente.")
    if activas_clientes == 0:
        print("\n[!] ADVERTENCIA: No hay usuarios suscritos a notificaciones push.")
        print("    Los usuarios deben instalar la PWA y dar permisos de notificaciones.")
else:
    print(f"[!] {fallos} check(s) fallaron. Revisa la configuracion.")

print("\n" + "=" * 80)
