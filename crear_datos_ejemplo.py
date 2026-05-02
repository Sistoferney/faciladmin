"""
Script para crear datos de ejemplo en FacilAdmin
Ejecuta: python crear_datos_ejemplo.py
"""
import os
import django
from datetime import datetime, timedelta

# Forzar modo EAGER (sin Redis) para este script
os.environ.setdefault('USE_CELERY_EAGER', 'True')

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from apps.authentication.models import Usuario
from apps.negocios.models import Negocio, ConfiguracionHorario
from apps.servicios.models import Servicio
from apps.clientes.models import Cliente
from apps.citas.models import Cita

def crear_datos_ejemplo():
    """Crear datos de ejemplo para el sistema"""

    print("🚀 Creando datos de ejemplo para FacilAdmin...\n")

    # 1. Obtener el usuario actual (el primero que encuentre)
    try:
        usuario = Usuario.objects.filter(is_superuser=True).first()
        if not usuario:
            print("❌ Error: No se encontró ningún superusuario.")
            print("   Ejecuta primero: python manage.py createsuperuser")
            return

        print(f"✓ Usuario encontrado: {usuario.email}")
    except Exception as e:
        print(f"❌ Error al buscar usuario: {e}")
        return

    # 2. Crear negocio si no existe
    negocio, created = Negocio.objects.get_or_create(
        administrador=usuario,
        defaults={
            'nombre': 'Spa & Belleza Ejemplo',
            'tipo': 'spa',
            'descripcion': 'Centro de belleza y relajación. Ofrecemos los mejores servicios para tu bienestar.',
            'telefono': '+52 55 1234 5678',
            'email': 'contacto@spaejemplo.com',
            'whatsapp': '+52 55 1234 5678',
            'direccion': 'Av. Principal 123, Col. Centro',
            'ciudad': 'Ciudad de México',
            'estado': 'CDMX',
            'codigo_postal': '06000',
            'horario_apertura': '09:00',
            'horario_cierre': '19:00',
            'dias_atencion': 'Lunes a Sábado',
            'requiere_abono': True,
            'porcentaje_abono': 50.00,
            'banco': 'Banco Ejemplo',
            'numero_cuenta': '1234567890',
            'clabe': '012345678901234567',
            'titular_cuenta': 'Spa & Belleza Ejemplo S.A.',
            'color_primario': '#E91E63',
            'color_secundario': '#9C27B0',
            'acepta_reservas_online': True,
            'facebook': 'https://facebook.com/spaejemplo',
            'instagram': 'https://instagram.com/spaejemplo',
        }
    )

    if created:
        print(f"✓ Negocio creado: {negocio.nombre}")
        print(f"  URL pública: {negocio.url_publica}")
    else:
        print(f"⚠ Negocio ya existía: {negocio.nombre}")

    # 3. Crear configuración de horarios
    dias_semana = [
        (0, 'Lunes', True, '09:00', '19:00'),
        (1, 'Martes', True, '09:00', '19:00'),
        (2, 'Miércoles', True, '09:00', '19:00'),
        (3, 'Jueves', True, '09:00', '19:00'),
        (4, 'Viernes', True, '09:00', '20:00'),
        (5, 'Sábado', True, '10:00', '18:00'),
        (6, 'Domingo', False, '09:00', '14:00'),
    ]

    for dia, nombre, abierto, apertura, cierre in dias_semana:
        ConfiguracionHorario.objects.get_or_create(
            negocio=negocio,
            dia_semana=dia,
            defaults={
                'esta_abierto': abierto,
                'hora_apertura': apertura,
                'hora_cierre': cierre,
            }
        )

    print("✓ Horarios configurados")

    # 4. Crear servicios
    servicios_data = [
        {
            'nombre': 'Corte de Cabello',
            'descripcion': 'Corte personalizado según tu estilo',
            'precio': 150.00,
            'duracion_minutos': 30,
            'frecuencia_dias': 30,
            'orden': 1,
        },
        {
            'nombre': 'Tinte Completo',
            'descripcion': 'Coloración profesional de cabello',
            'precio': 450.00,
            'duracion_minutos': 90,
            'frecuencia_dias': 45,
            'orden': 2,
        },
        {
            'nombre': 'Masaje Relajante',
            'descripcion': 'Masaje de cuerpo completo',
            'precio': 500.00,
            'duracion_minutos': 60,
            'frecuencia_dias': 15,
            'orden': 3,
        },
        {
            'nombre': 'Facial Profundo',
            'descripcion': 'Limpieza facial con tratamiento',
            'precio': 350.00,
            'duracion_minutos': 45,
            'frecuencia_dias': 20,
            'orden': 4,
        },
        {
            'nombre': 'Manicure y Pedicure',
            'descripcion': 'Tratamiento completo de manos y pies',
            'precio': 280.00,
            'duracion_minutos': 60,
            'frecuencia_dias': 14,
            'orden': 5,
        },
    ]

    servicios_creados = []
    for servicio_data in servicios_data:
        servicio, created = Servicio.objects.get_or_create(
            negocio=negocio,
            nombre=servicio_data['nombre'],
            defaults=servicio_data
        )
        servicios_creados.append(servicio)
        if created:
            print(f"✓ Servicio creado: {servicio.nombre} - ${servicio.precio}")

    # 5. Crear clientes de ejemplo
    clientes_data = [
        {
            'nombre': 'María González',
            'telefono': '+52 55 1111 1111',
            'email': 'maria@ejemplo.com',
            'tipo_cliente': 'frecuente',
        },
        {
            'nombre': 'Juan Pérez',
            'telefono': '+52 55 2222 2222',
            'email': 'juan@ejemplo.com',
            'tipo_cliente': 'nuevo',
        },
        {
            'nombre': 'Ana Martínez',
            'telefono': '+52 55 3333 3333',
            'email': 'ana@ejemplo.com',
            'tipo_cliente': 'frecuente',
        },
        {
            'nombre': 'Carlos López',
            'telefono': '+52 55 4444 4444',
            'email': 'carlos@ejemplo.com',
            'tipo_cliente': 'nuevo',
        },
    ]

    clientes_creados = []
    for cliente_data in clientes_data:
        cliente, created = Cliente.objects.get_or_create(
            negocio=negocio,
            telefono=cliente_data['telefono'],
            defaults={
                'nombre': cliente_data['nombre'],
                'email': cliente_data['email'],
                'tipo_cliente': cliente_data['tipo_cliente'],
                'acepta_whatsapp': True,
                'acepta_promociones': True,
            }
        )
        clientes_creados.append(cliente)
        if created:
            print(f"✓ Cliente creado: {cliente.nombre}")

    # 6. Crear citas de ejemplo
    print("\n✓ Creando citas de ejemplo...")

    # Cita para hoy
    hoy = timezone.now().replace(hour=14, minute=0, second=0, microsecond=0)

    citas_data = [
        {
            'cliente': clientes_creados[0],
            'servicio': servicios_creados[0],  # Corte
            'fecha_hora': hoy + timedelta(hours=2),
            'estado': 'confirmada',
            'origen': 'web',
        },
        {
            'cliente': clientes_creados[1],
            'servicio': servicios_creados[2],  # Masaje
            'fecha_hora': hoy + timedelta(days=1, hours=3),
            'estado': 'pendiente_abono',
            'origen': 'manual',
        },
        {
            'cliente': clientes_creados[2],
            'servicio': servicios_creados[4],  # Manicure
            'fecha_hora': hoy + timedelta(days=2, hours=1),
            'estado': 'confirmada',
            'origen': 'web',
        },
    ]

    for cita_data in citas_data:
        servicio = cita_data['servicio']
        cita, created = Cita.objects.get_or_create(
            negocio=negocio,
            cliente=cita_data['cliente'],
            servicio=servicio,
            fecha_hora=cita_data['fecha_hora'],
            defaults={
                'duracion_minutos': servicio.duracion_minutos,
                'estado': cita_data['estado'],
                'origen': cita_data['origen'],
            }
        )
        if created:
            print(f"  • {cita.cliente.nombre} - {cita.servicio.nombre} - {cita.fecha_hora.strftime('%d/%m/%Y %H:%M')}")

    print("\n" + "="*60)
    print("🎉 ¡Datos de ejemplo creados exitosamente!")
    print("="*60)
    print(f"\n📊 Resumen:")
    print(f"  • Negocio: {negocio.nombre}")
    print(f"  • Servicios: {len(servicios_creados)}")
    print(f"  • Clientes: {len(clientes_creados)}")
    print(f"  • Citas: {Cita.objects.filter(negocio=negocio).count()}")
    print(f"\n🌐 URL pública del negocio:")
    print(f"  {negocio.url_publica}")
    print(f"\n💻 Panel de administración:")
    print(f"  http://localhost:8000/admin")
    print("\n✅ ¡Ya puedes explorar el sistema!\n")

if __name__ == '__main__':
    try:
        crear_datos_ejemplo()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
