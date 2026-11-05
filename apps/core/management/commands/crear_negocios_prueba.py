"""
Crea negocios de prueba en el entorno local (nunca en producción).

    python manage.py crear_negocios_prueba            # crea los que falten
    python manage.py crear_negocios_prueba --borrar   # los borra y los crea de nuevo

Cubre los casos de la agenda:
- Uñas Bella: 3 especialistas (uno con horario propio, servicios distintos)
- Barbería El Parche: 2 especialistas que hacen todo
- Spa Serenidad: 1 especialista (una sola agenda)
- Peluquería Doña Rosa: sin especialistas (una sola agenda)

Y los de la marca: Uñas Bella usa degradado y Doña Rosa un color claro.

Todos los dueños entran con su celular y la contraseña CONTRASENA.
Las notificaciones se desactivan mientras se crean las citas.
"""
from datetime import datetime, time, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

CONTRASENA = 'prueba1234'

# Lunes=0 ... Domingo=6: (abre, cierra) o None si cierra
SEMANA_COMPLETA = {d: (time(8, 0), time(19, 0)) for d in range(6)} | {6: None}
SEMANA_CORTA = {d: (time(9, 0), time(18, 0)) for d in range(1, 6)} | {0: None, 6: None}

NEGOCIOS = [
    {
        'dueno': ('Valentina Ríos', '3009900001'),
        'nombre': 'Uñas Bella', 'tipo': 'salon_belleza', 'ciudad': 'Bogotá',
        'direccion': 'Calle 85 # 15-20', 'color': '#d63384',
        'color_secundario': '#6f42c1', 'degradado': True,
        'descripcion': 'Manicure, pedicure y pestañas en Chapinero. Atención con cita.',
        'horario': SEMANA_COMPLETA,
        'servicios': [
            ('Manicure tradicional', 30, 20000, False),
            ('Semipermanente', 60, 45000, True),
            ('Pedicure spa', 45, 30000, False),
            ('Pestañas pelo a pelo', 90, 90000, True),
        ],
        'especialistas': [
            {'nombre': 'Laura', 'cargo': 'Manicurista', 'servicios': ['Manicure tradicional', 'Semipermanente', 'Pedicure spa']},
            {'nombre': 'Sofía', 'cargo': 'Manicurista y lashista',
             'servicios': ['Semipermanente', 'Pestañas pelo a pelo'],
             'horario': {d: (time(10, 0), time(18, 0)) for d in range(1, 6)} | {0: None, 6: None}},
            {'nombre': 'Camila', 'cargo': 'Lashista', 'servicios': ['Pestañas pelo a pelo']},
        ],
    },
    {
        'dueno': ('Andrés Gómez', '3009900002'),
        'nombre': 'Barbería El Parche', 'tipo': 'barberia', 'ciudad': 'Medellín',
        'direccion': 'Carrera 70 # 44-10', 'color': '#212529',
        'descripcion': 'Cortes clásicos y modernos, arreglo de barba.',
        'horario': SEMANA_COMPLETA,
        'servicios': [
            ('Corte', 30, 25000, False),
            ('Barba', 20, 15000, False),
            ('Corte y barba', 45, 35000, False),
        ],
        'especialistas': [
            {'nombre': 'Andrés', 'cargo': 'Barbero', 'servicios': []},
            {'nombre': 'Julián', 'cargo': 'Barbero', 'servicios': []},
        ],
    },
    {
        'dueno': ('Marcela Torres', '3009900003'),
        'nombre': 'Spa Serenidad', 'tipo': 'spa', 'ciudad': 'Cali',
        'direccion': 'Avenida 6N # 23-50', 'color': '#198754',
        'descripcion': 'Masajes relajantes y faciales.',
        'horario': SEMANA_CORTA,
        'servicios': [
            ('Masaje relajante', 60, 80000, True),
            ('Limpieza facial', 50, 60000, False),
        ],
        'especialistas': [
            {'nombre': 'Marcela', 'cargo': 'Terapeuta', 'servicios': []},
        ],
    },
    {
        'dueno': ('Rosa Henao', '3009900004'),
        'nombre': 'Peluquería Doña Rosa', 'tipo': 'peluqueria', 'ciudad': 'La Estrella',
        'direccion': 'Calle 80 Sur # 60-12', 'color': '#ffd166',
        'descripcion': 'Peluquería de barrio: cortes, tintes y peinados.',
        'horario': SEMANA_COMPLETA,
        'servicios': [
            ('Corte dama', 40, 25000, False),
            ('Tinte', 90, 70000, True),
            ('Peinado', 45, 35000, False),
        ],
        'especialistas': [],
    },
]

CLIENTES = [
    ('Ana María López', '3109900101'), ('Juliana Pérez', '3109900102'),
    ('Carlos Ruiz', '3109900103'), ('Daniela Restrepo', '3109900104'),
    ('Santiago Mejía', '3109900105'), ('Paula Castaño', '3109900106'),
]


class Command(BaseCommand):
    help = 'Crea negocios de prueba en local (servicios, especialistas, clientes y citas)'

    def add_arguments(self, parser):
        parser.add_argument('--borrar', action='store_true', help='Borra los negocios de prueba antes de crearlos')

    def handle(self, *args, **opciones):
        if not settings.DEBUG:
            raise CommandError('Solo se puede usar en el entorno local (DEBUG=True).')

        from apps.authentication.models import Usuario

        if opciones['borrar']:
            telefonos = [n['dueno'][1] for n in NEGOCIOS]
            from apps.authentication.telefonos import normalizar_telefono
            borrados = Usuario.objects.filter(
                telefono__in=[normalizar_telefono(t) for t in telefonos], is_superuser=False
            )
            total = borrados.count()
            borrados.delete()  # en cascada: negocio, servicios, clientes, citas
            self.stdout.write(f'Borrados {total} negocios de prueba.')

        # Sin notificaciones mientras se crean las citas de ejemplo
        with patch('apps.notificaciones.tasks.programar_notificacion'):
            for datos in NEGOCIOS:
                self._crear_negocio(datos)

        self.stdout.write(self.style.SUCCESS('\nListo. Para entrar al panel: /login/ con el celular y la contraseña'))
        self.stdout.write(f'Contraseña de todos: {CONTRASENA}\n')
        from apps.negocios.models import Negocio
        for datos in NEGOCIOS:
            negocio = Negocio.objects.filter(nombre=datos['nombre']).first()
            if negocio:
                self.stdout.write(
                    f"  {datos['nombre']:<24} dueño {datos['dueno'][1]}  "
                    f"especialistas {negocio.especialistas.count()}  ->  /{negocio.slug}/  y  /{negocio.slug}/admin/"
                )

    @transaction.atomic
    def _crear_negocio(self, datos):
        from apps.authentication.models import Usuario
        from apps.authentication.telefonos import normalizar_telefono
        from apps.negocios.models import ConfiguracionHorario, Especialista, HorarioEspecialista, Negocio
        from apps.servicios.models import Servicio

        nombre_dueno, telefono = datos['dueno']
        if Usuario.objects.filter(telefono=normalizar_telefono(telefono)).exists():
            self.stdout.write(f"Ya existe {datos['nombre']} (usa --borrar para recrearlo).")
            return

        dueno = Usuario.objects.create_user(
            telefono=telefono, password=CONTRASENA, nombre=nombre_dueno,
            email=f'dueno{telefono[-1]}@prueba.local',
        )
        negocio = Negocio.objects.create(
            administrador=dueno, nombre=datos['nombre'], tipo=datos['tipo'], telefono=telefono,
            whatsapp=telefono, ciudad=datos['ciudad'], direccion=datos['direccion'],
            descripcion=datos['descripcion'], color_primario=datos['color'],
            color_secundario=datos.get('color_secundario', '#6c757d'),
            usar_degradado=datos.get('degradado', False),
            horario_apertura=time(8, 0), horario_cierre=time(19, 0),
            nequi=telefono, porcentaje_abono=Decimal('30'),
        )
        for dia, horas in datos['horario'].items():
            ConfiguracionHorario.objects.create(
                negocio=negocio, dia_semana=dia, esta_abierto=horas is not None,
                hora_apertura=horas[0] if horas else time(8, 0),
                hora_cierre=horas[1] if horas else time(18, 0),
            )

        servicios = {}
        for orden, (nombre, minutos, precio, abono) in enumerate(datos['servicios']):
            servicios[nombre] = Servicio.objects.create(
                negocio=negocio, nombre=nombre, duracion_minutos=minutos, precio=Decimal(precio),
                frecuencia_dias=30, orden=orden, requiere_abono=abono,
                porcentaje_abono=Decimal('30') if abono else None,
            )

        for orden, e in enumerate(datos['especialistas']):
            especialista = Especialista.objects.create(
                negocio=negocio, nombre=e['nombre'], cargo=e['cargo'], orden=orden,
                usa_horario_negocio='horario' not in e,
            )
            especialista.servicios.set([servicios[s] for s in e['servicios']])
            for dia, horas in e.get('horario', {}).items():
                HorarioEspecialista.objects.create(
                    especialista=especialista, dia_semana=dia, esta_abierto=horas is not None,
                    hora_apertura=horas[0] if horas else time(9, 0),
                    hora_cierre=horas[1] if horas else time(18, 0),
                )

        clientes = self._crear_clientes(negocio)
        citas = self._crear_citas(negocio, list(servicios.values()), clientes)
        self.stdout.write(f"Creado {datos['nombre']}: {len(servicios)} servicios, "
                          f"{len(datos['especialistas'])} especialistas, {len(clientes)} clientes, {citas} citas.")

    def _crear_clientes(self, negocio):
        from apps.clientes.models import Cliente
        return [
            Cliente.objects.create(negocio=negocio, nombre=nombre, telefono=telefono, creado_manualmente=True)
            for nombre, telefono in CLIENTES
        ]

    def _crear_citas(self, negocio, servicios, clientes):
        """
        Historial (citas completadas hace 10-50 días) y próximas citas en los
        siguientes días, validando la disponibilidad como lo hace la reserva.
        """
        from apps.abonos.models import Abono
        from apps.citas.models import Cita
        from apps.negocios.disponibilidad import resolver_especialista

        creadas = 0
        hoy = timezone.localdate()

        # Historial: una visita completada por cliente
        for i, cliente in enumerate(clientes):
            servicio = servicios[i % len(servicios)]
            fecha = hoy - timedelta(days=10 + i * 8)
            Cita.objects.create(
                negocio=negocio, cliente=cliente, servicio=servicio,
                fecha_hora=timezone.make_aware(datetime.combine(fecha, time(10, 0))),
                duracion_minutos=servicio.duracion_minutos, estado='completada', origen='web',
            )
            cliente.actualizar_estadisticas()
            creadas += 1

        # Próximas citas: varias por día en distintas horas
        horas = [time(9, 0), time(10, 0), time(11, 0), time(14, 0), time(15, 30), time(17, 0)]
        n = 0
        for dias in range(1, 8):
            fecha = hoy + timedelta(days=dias)
            for hora in horas[:3 + dias % 3]:
                servicio = servicios[n % len(servicios)]
                cliente = clientes[n % len(clientes)]
                n += 1
                fecha_hora = timezone.make_aware(datetime.combine(fecha, hora))
                disponible, especialista = resolver_especialista(negocio, fecha_hora, servicio, 'cualquiera')
                if not disponible:
                    continue
                exige_abono = servicio.requiere_pago_abono and dias >= 3 and n % 2 == 0
                cita = Cita.objects.create(
                    negocio=negocio, cliente=cliente, servicio=servicio, fecha_hora=fecha_hora,
                    duracion_minutos=servicio.duracion_minutos, especialista=especialista,
                    estado='pendiente_abono' if exige_abono else 'confirmada',
                    origen='web' if n % 3 else 'manual',
                )
                if exige_abono:
                    Abono.objects.create(
                        cita=cita, monto=servicio.precio_abono, metodo_pago='transferencia',
                        estado='pendiente', fecha_limite=cita.fecha_limite_abono,
                    )
                creadas += 1
        return creadas
