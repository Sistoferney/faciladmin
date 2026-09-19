"""
Comando para verificar suscripciones de admin en la base de datos
Uso: python manage.py verificar_suscripciones_admin
"""
from django.core.management.base import BaseCommand
from apps.notificaciones.models import UsuarioPushSubscription, ClientePushSubscription
from apps.negocios.models import Negocio
from django.utils import timezone


class Command(BaseCommand):
    help = 'Verifica las suscripciones push de administradores en la base de datos'

    def handle(self, *args, **options):
        self.stdout.write("="*70)
        self.stdout.write(self.style.SUCCESS("VERIFICACION DE SUSCRIPCIONES PUSH DE ADMIN"))
        self.stdout.write("="*70)

        # 1. Suscripciones de admin
        self.stdout.write("\n1. SUSCRIPCIONES DE ADMINISTRADORES:")
        total_admin = UsuarioPushSubscription.objects.count()
        activas_admin = UsuarioPushSubscription.objects.filter(activa=True).count()

        self.stdout.write(f"   - Total suscripciones: {total_admin}")
        self.stdout.write(f"   - Suscripciones activas: {activas_admin}")

        if total_admin > 0:
            self.stdout.write("\n   Detalles:")
            for sub in UsuarioPushSubscription.objects.all():
                estado = "ACTIVA" if sub.activa else "INACTIVA"
                self.stdout.write(f"\n   - Suscripcion ID: {sub.id} [{estado}]")
                self.stdout.write(f"     User: {sub.user.username}")
                self.stdout.write(f"     Negocio: {sub.negocio.nombre} (slug: {sub.negocio.slug})")
                self.stdout.write(f"     Endpoint: {sub.endpoint[:60]}...")
                self.stdout.write(f"     Creada: {sub.fecha_creacion}")
                self.stdout.write(f"     User-Agent: {sub.user_agent[:50]}...")
        else:
            self.stdout.write(self.style.WARNING("\n   ¡NO HAY SUSCRIPCIONES DE ADMIN!"))
            self.stdout.write("   Esto significa que ningun admin se ha suscrito a las notificaciones.")

        # 2. Suscripciones de clientes
        self.stdout.write("\n2. SUSCRIPCIONES DE CLIENTES:")
        total_cliente = ClientePushSubscription.objects.count()
        activas_cliente = ClientePushSubscription.objects.filter(activa=True).count()

        self.stdout.write(f"   - Total suscripciones: {total_cliente}")
        self.stdout.write(f"   - Suscripciones activas: {activas_cliente}")

        # 3. Negocios
        self.stdout.write("\n3. NEGOCIOS EN EL SISTEMA:")
        negocios = Negocio.objects.all()
        self.stdout.write(f"   - Total negocios: {negocios.count()}")

        for negocio in negocios:
            self.stdout.write(f"\n   - {negocio.nombre} (slug: {negocio.slug})")
            self.stdout.write(f"     Administrador: {negocio.administrador.username if negocio.administrador else 'Sin admin'}")

            # Contar suscripciones de este negocio
            subs_negocio = UsuarioPushSubscription.objects.filter(
                negocio=negocio,
                activa=True
            ).count()
            self.stdout.write(f"     Suscripciones admin activas: {subs_negocio}")

        # 4. Resumen y recomendaciones
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("RESUMEN:"))
        self.stdout.write("="*70)

        if activas_admin == 0:
            self.stdout.write(self.style.ERROR("\n¡PROBLEMA ENCONTRADO!"))
            self.stdout.write("No hay suscripciones de admin activas en la base de datos.")
            self.stdout.write("\nPosibles causas:")
            self.stdout.write("1. El admin nunca activo las notificaciones en la PWA")
            self.stdout.write("2. La API de suscripcion fallo al guardar")
            self.stdout.write("3. Los permisos del navegador fueron bloqueados")
            self.stdout.write("\nSolucion:")
            self.stdout.write("1. Abre la PWA de admin en el dispositivo")
            self.stdout.write("2. Ve a 'Diagnostico de Notificaciones'")
            self.stdout.write("3. Verifica que los permisos esten activados")
            self.stdout.write("4. Haz clic en 'Activar Notificaciones' si es necesario")
        else:
            self.stdout.write(self.style.SUCCESS(f"\n✓ Hay {activas_admin} suscripciones activas"))
            self.stdout.write("Las notificaciones deberian estar funcionando correctamente.")

        self.stdout.write("\n" + "="*70 + "\n")
