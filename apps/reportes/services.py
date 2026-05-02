"""
Servicios para generar reportes
RF-38, RF-39
"""
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta
from apps.citas.models import Cita
from apps.clientes.models import Cliente


class ReporteService:
    """Servicio para generar reportes del negocio"""

    def __init__(self, negocio):
        self.negocio = negocio

    def reporte_general(self, fecha_inicio=None, fecha_fin=None):
        """
        RF-38: Reporte general con:
        - Número de citas
        - Clientes recurrentes
        - Ingresos estimados
        """
        if not fecha_inicio:
            fecha_inicio = timezone.now() - timedelta(days=30)
        if not fecha_fin:
            fecha_fin = timezone.now()

        citas = Cita.objects.filter(
            negocio=self.negocio,
            fecha_hora__gte=fecha_inicio,
            fecha_hora__lte=fecha_fin
        )

        # Número de citas
        total_citas = citas.count()
        citas_completadas = citas.filter(estado='completada').count()
        citas_canceladas = citas.filter(estado='cancelada').count()
        citas_pendientes = citas.filter(estado__in=['pendiente_abono', 'confirmada']).count()

        # Ingresos estimados
        ingresos_completados = sum(
            cita.servicio.precio for cita in citas.filter(estado='completada')
        )
        ingresos_potenciales = sum(
            cita.servicio.precio for cita in citas.filter(estado__in=['pendiente_abono', 'confirmada'])
        )

        # Clientes recurrentes (3 o más citas)
        clientes_frecuentes = Cliente.objects.filter(
            negocio=self.negocio,
            total_citas__gte=3
        ).count()

        return {
            'periodo': {
                'inicio': fecha_inicio,
                'fin': fecha_fin
            },
            'citas': {
                'total': total_citas,
                'completadas': citas_completadas,
                'canceladas': citas_canceladas,
                'pendientes': citas_pendientes
            },
            'ingresos': {
                'completados': ingresos_completados,
                'potenciales': ingresos_potenciales,
                'total_estimado': ingresos_completados + ingresos_potenciales
            },
            'clientes': {
                'total': Cliente.objects.filter(negocio=self.negocio, esta_activo=True).count(),
                'frecuentes': clientes_frecuentes,
                'nuevos': Cliente.objects.filter(negocio=self.negocio, tipo_cliente='nuevo').count(),
                'inactivos': Cliente.objects.filter(negocio=self.negocio, tipo_cliente='inactivo').count()
            }
        }

    def horarios_baja_ocupacion(self, dias_analisis=30):
        """
        RF-39: Identifica horarios con baja ocupación
        """
        fecha_inicio = timezone.now() - timedelta(days=dias_analisis)

        citas = Cita.objects.filter(
            negocio=self.negocio,
            fecha_hora__gte=fecha_inicio,
            estado__in=['completada', 'confirmada']
        )

        # Agrupar por hora del día
        ocupacion_por_hora = {}
        for hora in range(24):
            ocupacion_por_hora[hora] = citas.filter(
                fecha_hora__hour=hora
            ).count()

        # Identificar horas con baja ocupación (menos del 20% del promedio)
        if citas.count() > 0:
            promedio = sum(ocupacion_por_hora.values()) / len(ocupacion_por_hora)
            umbral_bajo = promedio * 0.2

            horas_baja_ocupacion = [
                {'hora': hora, 'citas': count}
                for hora, count in ocupacion_por_hora.items()
                if count < umbral_bajo
            ]
        else:
            horas_baja_ocupacion = []

        # Agrupar por día de la semana
        ocupacion_por_dia = {}
        for dia in range(7):
            ocupacion_por_dia[dia] = citas.filter(
                fecha_hora__week_day=dia
            ).count()

        return {
            'periodo_analisis': dias_analisis,
            'ocupacion_por_hora': ocupacion_por_hora,
            'horas_baja_ocupacion': horas_baja_ocupacion,
            'ocupacion_por_dia': ocupacion_por_dia,
            'total_citas_analizadas': citas.count()
        }

    def servicios_mas_solicitados(self, limite=10):
        """Servicios más solicitados"""
        from apps.servicios.models import Servicio
        from django.db.models import Count

        servicios = Servicio.objects.filter(
            negocio=self.negocio
        ).annotate(
            total_citas=Count('citas')
        ).order_by('-total_citas')[:limite]

        return [
            {
                'servicio': servicio.nombre,
                'total_citas': servicio.total_citas,
                'precio': servicio.precio,
                'ingresos_generados': servicio.total_citas * servicio.precio
            }
            for servicio in servicios
        ]

    def tasa_cancelacion(self, dias=30):
        """Calcula tasa de cancelación"""
        fecha_inicio = timezone.now() - timedelta(days=dias)

        citas = Cita.objects.filter(
            negocio=self.negocio,
            fecha_hora__gte=fecha_inicio
        )

        total = citas.count()
        canceladas = citas.filter(estado='cancelada').count()
        no_asistio = citas.filter(estado='no_asistio').count()

        if total > 0:
            tasa_cancelacion = (canceladas / total) * 100
            tasa_no_asistencia = (no_asistio / total) * 100
        else:
            tasa_cancelacion = 0
            tasa_no_asistencia = 0

        return {
            'total_citas': total,
            'canceladas': canceladas,
            'no_asistio': no_asistio,
            'tasa_cancelacion': round(tasa_cancelacion, 2),
            'tasa_no_asistencia': round(tasa_no_asistencia, 2)
        }
