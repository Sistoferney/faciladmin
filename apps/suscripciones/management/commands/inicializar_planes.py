"""
Management command para crear los planes de suscripción básicos
Ejecutar con: python manage.py inicializar_planes
"""
from django.core.management.base import BaseCommand
from apps.suscripciones.models import PlanSuscripcion


class Command(BaseCommand):
    help = 'Crea los planes de suscripción básicos (Trial y Mensual)'

    def handle(self, *args, **options):
        self.stdout.write('Inicializando planes de suscripción...\n')

        # Plan Trial (120 días gratis)
        plan_trial, created = PlanSuscripcion.objects.get_or_create(
            tipo='trial',
            defaults={
                'nombre': 'Trial Gratuito',
                'precio': 0.00,
                'duracion_dias': 120,
                'descripcion': 'Período de prueba gratis de 120 días con acceso completo a todas las funciones',
                'activo': True,
                # Límites (None = ilimitado para trial)
                'max_citas_mes': None,
                'max_servicios': None,
                'max_clientes': None,
                'push_notifications': True,
                'soporte_prioritario': False,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Plan Trial creado: {plan_trial}'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠ Plan Trial ya existía: {plan_trial}'))

        # Plan Mensual ($25.000)
        plan_mensual, created = PlanSuscripcion.objects.get_or_create(
            tipo='mensual',
            defaults={
                'nombre': 'Plan Mensual',
                'precio': 25000.00,
                'duracion_dias': 30,
                'descripcion': 'Plan mensual con acceso completo por 30 días',
                'activo': True,
                # Límites (None = ilimitado para plan mensual también)
                'max_citas_mes': None,
                'max_servicios': None,
                'max_clientes': None,
                'push_notifications': True,
                'soporte_prioritario': False,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Plan Mensual creado: {plan_mensual}'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠ Plan Mensual ya existía: {plan_mensual}'))

        # Resumen
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('PLANES DE SUSCRIPCIÓN INICIALIZADOS'))
        self.stdout.write('='*60)

        planes = PlanSuscripcion.objects.all()
        for plan in planes:
            self.stdout.write(f'\n📋 {plan.nombre}')
            self.stdout.write(f'   Tipo: {plan.get_tipo_display()}')
            self.stdout.write(f'   Precio: ${plan.precio}')
            self.stdout.write(f'   Duración: {plan.duracion_dias} días')
            self.stdout.write(f'   Activo: {"Sí" if plan.activo else "No"}')

        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('✓ Listo! Ya puedes crear usuarios nuevos.\n'))
