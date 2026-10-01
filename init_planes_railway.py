#!/usr/bin/env python
"""
Script rápido para inicializar planes de suscripción en Railway
Ejecutar: railway run python init_planes_railway.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from apps.suscripciones.models import PlanSuscripcion

print("=" * 60)
print("INICIALIZANDO PLANES DE SUSCRIPCIÓN EN RAILWAY")
print("=" * 60)

# Plan Trial
plan_trial, created = PlanSuscripcion.objects.get_or_create(
    tipo='trial',
    defaults={
        'nombre': 'Trial Gratuito',
        'precio': 0.00,
        'duracion_dias': 120,
        'descripcion': 'Período de prueba gratis de 120 días con acceso completo',
        'activo': True,
        'max_citas_mes': None,
        'max_servicios': None,
        'max_clientes': None,
        'push_notifications': True,
        'soporte_prioritario': False,
    }
)

if created:
    print(f"✓ Plan Trial CREADO: {plan_trial}")
else:
    print(f"⚠ Plan Trial ya existía: {plan_trial}")

# Plan Mensual
plan_mensual, created = PlanSuscripcion.objects.get_or_create(
    tipo='mensual',
    defaults={
        'nombre': 'Plan Mensual',
        'precio': 25000.00,
        'duracion_dias': 30,
        'descripcion': 'Plan mensual con acceso completo por 30 días',
        'activo': True,
        'max_citas_mes': None,
        'max_servicios': None,
        'max_clientes': None,
        'push_notifications': True,
        'soporte_prioritario': False,
    }
)

if created:
    print(f"✓ Plan Mensual CREADO: {plan_mensual}")
else:
    print(f"⚠ Plan Mensual ya existía: {plan_mensual}")

print("\n" + "=" * 60)
print("PLANES DISPONIBLES:")
print("=" * 60)

for plan in PlanSuscripcion.objects.all():
    print(f"\n📋 {plan.nombre}")
    print(f"   Tipo: {plan.get_tipo_display()}")
    print(f"   Precio: ${plan.precio}")
    print(f"   Duración: {plan.duracion_dias} días")
    print(f"   Activo: {'Sí' if plan.activo else 'No'}")

print("\n" + "=" * 60)
print("✓ INICIALIZACIÓN COMPLETA")
print("=" * 60)
