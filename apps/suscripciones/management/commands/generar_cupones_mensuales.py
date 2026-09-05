"""
Comando para generar cupones mensuales automáticamente
para los participantes del programa de referidos que cumplan requisitos.

Uso:
    python manage.py generar_cupones_mensuales

Este comando debe ejecutarse mensualmente mediante un cron job o tarea programada.
"""

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from apps.suscripciones.models import ProgramaReferidos


class Command(BaseCommand):
    help = 'Genera cupones mensuales para participantes del programa de referidos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula la generación sin crear cupones reales',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('Modo DRY RUN: No se crearán cupones reales\n'))

        # Obtener todos los programas activos
        programas = ProgramaReferidos.objects.filter(activo=True)
        total_programas = programas.count()

        self.stdout.write(f'Encontrados {total_programas} programa(s) activo(s)\n')

        # Contadores
        cupones_generados = 0
        errores = 0
        ya_generados = 0

        for programa in programas:
            # Actualizar estado (por si algún referido se desactivó)
            programa.actualizar_estado()

            # Verificar si puede generar cupón
            puede, mensaje = programa.puede_generar_cupon()

            if not puede:
                if 'Ya generaste' in mensaje:
                    ya_generados += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠️  {programa.negocio.nombre}: {mensaje}'
                        )
                    )
                else:
                    errores += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'✗ {programa.negocio.nombre}: {mensaje}'
                        )
                    )
                continue

            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'[DRY RUN] ✓ Se generaría cupón para: {programa.negocio.nombre}'
                    )
                )
                cupones_generados += 1
                continue

            # Generar cupón real
            exito, mensaje_gen, cupon = programa.generar_cupon_mensual()

            if exito:
                cupones_generados += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ {programa.negocio.nombre}: {mensaje_gen}'
                    )
                )

                # Enviar email de notificación
                try:
                    admin_email = programa.negocio.administrador.email
                    admin_nombre = programa.negocio.administrador.nombre or 'Admin'

                    send_mail(
                        subject='🎁 Tu cupón mensual está listo - FacilAdmin',
                        message=f'''
Hola {admin_nombre},

¡Excelente noticia! Has ganado tu cupón mensual por el programa de referidos de FacilAdmin.

📋 Código del cupón: {cupon.codigo}
⏰ Válido hasta: {cupon.fecha_expiracion.strftime('%d/%m/%Y')}
🎯 Beneficio: 1 mes gratis (30 días)

Para canjear tu cupón:
1. Ingresa a tu panel de suscripciones
2. Haz clic en "Canjear cupón"
3. Ingresa el código: {cupon.codigo}

Tu cupón se generó automáticamente porque tienes 3 referidos activos:
- {programa.negocio_referido_1.nombre if programa.negocio_referido_1 else 'N/A'}
- {programa.negocio_referido_2.nombre if programa.negocio_referido_2 else 'N/A'}
- {programa.negocio_referido_3.nombre if programa.negocio_referido_3 else 'N/A'}

¡Gracias por recomendar FacilAdmin!

Saludos,
El equipo de FacilAdmin
                        ''',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[admin_email],
                        fail_silently=True,
                    )

                    self.stdout.write(
                        self.style.SUCCESS(
                            f'   └─ Email enviado a {admin_email}'
                        )
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f'   └─ Error al enviar email: {str(e)}'
                        )
                    )

            else:
                errores += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ {programa.negocio.nombre}: {mensaje_gen}'
                    )
                )

        # Resumen final
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'\nRESUMEN:'))
        self.stdout.write(f'Total programas activos: {total_programas}')
        self.stdout.write(self.style.SUCCESS(f'Cupones generados: {cupones_generados}'))
        self.stdout.write(self.style.WARNING(f'Ya generados este mes: {ya_generados}'))
        self.stdout.write(self.style.ERROR(f'Errores/No cumplen: {errores}'))

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️  Esto fue una simulación. Ejecuta sin --dry-run para generar cupones reales.'
                )
            )
