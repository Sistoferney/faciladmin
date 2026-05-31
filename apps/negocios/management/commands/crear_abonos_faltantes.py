from django.core.management.base import BaseCommand
from apps.citas.models import Cita
from apps.abonos.models import Abono


class Command(BaseCommand):
    help = 'Crea registros de Abono para citas con estado pendiente_abono que no tienen abono'

    def handle(self, *args, **kwargs):
        self.stdout.write('Buscando citas sin abono...\n')

        # Buscar citas con estado pendiente_abono
        citas_sin_abono = []
        citas_pendientes = Cita.objects.filter(estado='pendiente_abono').select_related('servicio', 'cliente', 'negocio')

        for cita in citas_pendientes:
            # Verificar si ya tiene abono
            if not hasattr(cita, 'abono'):
                citas_sin_abono.append(cita)

        if not citas_sin_abono:
            self.stdout.write(self.style.WARNING('No se encontraron citas sin abono'))
            return

        self.stdout.write(f'Encontradas {len(citas_sin_abono)} citas sin abono\n')

        abonos_creados = 0
        for cita in citas_sin_abono:
            try:
                abono = Abono.objects.create(
                    cita=cita,
                    monto=cita.servicio.precio_abono,
                    metodo_pago='transferencia',
                    estado='pendiente',
                    fecha_limite=cita.fecha_limite_abono
                )
                abonos_creados += 1
                self.stdout.write(self.style.SUCCESS(
                    f'Abono creado para cita #{cita.id} - Cliente: {cita.cliente.nombre} - Monto: ${abono.monto}'
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'Error al crear abono para cita #{cita.id}: {e}'
                ))

        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'Se crearon {abonos_creados} abonos'))
        self.stdout.write('='*60 + '\n')
