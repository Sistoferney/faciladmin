"""
Vistas del superadministrador de FacilAdmin (dueño de la plataforma)
"""
from datetime import timedelta

from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.paginator import Paginator
from django.db.models import Count, Exists, F, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce
from django.http import Http404
from django.shortcuts import render
from django.utils import timezone

from apps.citas.models import Cita
from apps.clientes.models import Cliente
from apps.core.whatsapp import enlace_whatsapp
from apps.negocios.models import Negocio
from apps.notificaciones.models import UsuarioPushSubscription

# Sin citas nuevas ni ingresos del dueño en este tiempo: negocio "sin actividad"
DIAS_ACTIVIDAD = 30
POR_PAGINA = 25

ORDENES = {
    'recientes': ['-fecha_creacion'],
    'actividad': [F('ultima_cita').desc(nulls_last=True), '-fecha_creacion'],
    'citas': ['-citas_30d', '-fecha_creacion'],
    'nombre': ['nombre'],
}



def superadmin_required(vista):
    """Solo el superadministrador; para los demás la página no existe"""
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not request.user.is_superuser:
            raise Http404
        return vista(request, *args, **kwargs)
    return envoltura


def _contar(modelo, **filtros):
    """Subconsulta que cuenta filas relacionadas con el negocio (evita multiplicar joins)"""
    return Coalesce(Subquery(
        modelo.objects.filter(negocio=OuterRef('pk'), **filtros)
        .order_by().values('negocio').annotate(total=Count('pk')).values('total')[:1]
    ), 0)


def _sin_actividad(hace):
    return (
        (Q(ultima_cita__lt=hace) | Q(ultima_cita__isnull=True))
        & (Q(administrador__last_login__lt=hace) | Q(administrador__last_login__isnull=True))
    )


@superadmin_required
def negocios_superadmin(request):
    """
    Negocios inscritos, con indicadores de uso para saber a quién ayudar:
    citas del último mes, clientes, última actividad, notificaciones y plan.
    """
    ahora = timezone.now()
    hace = ahora - timedelta(days=DIAS_ACTIVIDAD)
    inicio_mes = timezone.localtime(ahora).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    negocios = Negocio.objects.select_related('administrador', 'suscripcion__plan').annotate(
        citas_30d=_contar(Cita, fecha_creacion__gte=hace),
        total_clientes=_contar(Cliente),
        ultima_cita=Subquery(
            Cita.objects.filter(negocio=OuterRef('pk')).order_by('-fecha_creacion').values('fecha_creacion')[:1]
        ),
        push_activo=Exists(UsuarioPushSubscription.objects.filter(negocio=OuterRef('pk'), activa=True)),
    )

    resumen = {
        'total': negocios.count(),
        'activos': negocios.filter(esta_activo=True).count(),
        'nuevos_mes': negocios.filter(fecha_creacion__gte=inicio_mes).count(),
        'sin_actividad': negocios.filter(esta_activo=True).filter(_sin_actividad(hace)).count(),
    }

    q = request.GET.get('q', '').strip()
    if q:
        filtro = (
            Q(nombre__icontains=q) | Q(slug__icontains=q)
            | Q(administrador__nombre__icontains=q) | Q(administrador__email__icontains=q)
        )
        digitos = ''.join(c for c in q if c.isdigit())
        if len(digitos) >= 4:
            filtro |= Q(administrador__telefono__contains=digitos) | Q(telefono__contains=digitos)
        negocios = negocios.filter(filtro)

    estado = request.GET.get('estado', 'activos')
    if estado == 'activos':
        negocios = negocios.filter(esta_activo=True)
    elif estado == 'inactivos':
        negocios = negocios.filter(esta_activo=False)
    elif estado == 'sin_actividad':
        negocios = negocios.filter(esta_activo=True).filter(_sin_actividad(hace))

    orden = request.GET.get('orden', 'recientes')
    negocios = negocios.order_by(*ORDENES.get(orden, ORDENES['recientes']))

    pagina = Paginator(negocios, POR_PAGINA).get_page(request.GET.get('pagina'))
    for negocio in pagina:
        admin = negocio.administrador
        fechas = [f for f in (negocio.ultima_cita, admin.last_login) if f]
        negocio.ultima_actividad = max(fechas) if fechas else None
        negocio.inactivo_reciente = not negocio.ultima_actividad or negocio.ultima_actividad < hace
        negocio.whatsapp_dueno = enlace_whatsapp(
            admin.telefono,
            f'Hola {admin.nombre}, te escribo de FacilAdmin sobre {negocio.nombre}.',
        ) if admin.telefono else ''

    # Para conservar búsqueda y filtros al cambiar de página
    parametros = request.GET.copy()
    parametros.pop('pagina', None)

    return render(request, 'superadmin/negocios.html', {
        'title': 'Negocios - FacilAdmin',
        'pagina': pagina,
        'resumen': resumen,
        'q': q,
        'estado': estado,
        'orden': orden,
        'parametros': parametros.urlencode(),
        'dias_actividad': DIAS_ACTIVIDAD,
    })
