"""
Seguimiento de clientes según la frecuencia de su servicio habitual.

Para cada cliente se toma su última visita (cita completada) y la frecuencia
del servicio de esa visita (Servicio.frecuencia_dias):

- Frecuencia + 2 días sin volver   -> se le envía UN recordatorio para agendar
                                      (una vez por ausencia; tarea diaria 11:00)
- Frecuencia + 50% sin volver      -> "Cliente por recuperar" (lista del panel,
                                      el dueño le escribe por WhatsApp)
- Servicio sin frecuencia          -> sin recordatorio; por recuperar a los 90 días
- Si tiene una cita próxima (pendiente o confirmada) no aplica nada de esto.

Se calcula al momento (no se guarda una etiqueta), así siempre está al día.
"""
from dataclasses import dataclass
from datetime import datetime

from django.utils import timezone

DIAS_EXTRA_RECORDATORIO = 2
FACTOR_RECUPERAR = 1.5
DIAS_RECUPERAR_SIN_FRECUENCIA = 90


@dataclass
class Seguimiento:
    cliente: object
    ultima_cita: object          # última cita completada
    dias_sin_venir: int
    frecuencia: int | None       # días; None si el servicio no la tiene

    @property
    def servicio(self):
        return self.ultima_cita.servicio

    @property
    def dias_recordatorio(self):
        """Días a partir de los cuales se le recuerda agendar (None: no aplica)"""
        return self.frecuencia + DIAS_EXTRA_RECORDATORIO if self.frecuencia else None

    @property
    def dias_recuperar(self):
        if self.frecuencia:
            return int(self.frecuencia * FACTOR_RECUPERAR)
        return DIAS_RECUPERAR_SIN_FRECUENCIA

    @property
    def toca_recordatorio(self):
        return self.dias_recordatorio is not None and self.dias_sin_venir >= self.dias_recordatorio

    @property
    def por_recuperar(self):
        return self.dias_sin_venir >= self.dias_recuperar


def seguimientos(negocio=None, ahora=None):
    """
    Seguimiento de cada cliente que tiene al menos una cita completada y no
    tiene citas próximas. negocio=None: todos los negocios activos.
    """
    from apps.citas.models import Cita

    ahora = ahora or timezone.now()
    completadas = Cita.objects.filter(estado='completada').select_related('cliente', 'servicio', 'negocio')
    proximas = Cita.objects.filter(estado__in=['pendiente_abono', 'confirmada'], fecha_hora__gt=ahora)
    if negocio is not None:
        completadas = completadas.filter(negocio=negocio)
        proximas = proximas.filter(negocio=negocio)
    else:
        completadas = completadas.filter(negocio__esta_activo=True)

    con_cita_proxima = set(proximas.values_list('cliente_id', flat=True))

    # Última cita completada de cada cliente (la primera al ordenar por fecha descendente)
    ultimas = {}
    for cita in completadas.order_by('cliente_id', '-fecha_hora'):
        if cita.cliente_id not in ultimas:
            ultimas[cita.cliente_id] = cita

    resultado = []
    for cliente_id, cita in ultimas.items():
        if cliente_id in con_cita_proxima or not cita.cliente.esta_activo:
            continue
        resultado.append(Seguimiento(
            cliente=cita.cliente,
            ultima_cita=cita,
            dias_sin_venir=(ahora - cita.fecha_hora).days,
            frecuencia=cita.servicio.frecuencia_dias or None,
        ))
    return resultado


def clientes_por_recuperar(negocio):
    """Clientes que superaron la frecuencia + 50% (o 90 días), del que más tiempo lleva al que menos"""
    lista = [s for s in seguimientos(negocio) if s.por_recuperar]
    return sorted(lista, key=lambda s: s.dias_sin_venir, reverse=True)
