"""
Vistas de administración personalizadas para cada mini-página
Panel de administración intuitivo para dueños de negocios
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum, Q
from datetime import timedelta
from .models import Negocio
from apps.servicios.models import Servicio
from apps.clientes.models import Cliente
from apps.citas.models import Cita
from apps.abonos.models import Abono


def admin_required(view_func):
    """
    Decorador para verificar que el usuario sea el admin del negocio
    """
    def wrapper(request, slug, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Debes iniciar sesión para acceder al panel de administración.')
            return redirect('/')

        negocio = get_object_or_404(Negocio, slug=slug)

        # Verificar que el usuario sea el admin de este negocio o superadmin
        if not (hasattr(request.user, 'negocio') and request.user.negocio == negocio) and not request.user.is_superuser:
            messages.error(request, 'No tienes permiso para acceder a este panel de administración.')
            return redirect('/')

        return view_func(request, slug, *args, **kwargs)

    return wrapper


@admin_required
def dashboard_admin(request, slug):
    """
    Dashboard principal del administrador
    Muestra resumen de citas, clientes, ingresos, etc.
    """
    negocio = get_object_or_404(Negocio, slug=slug)
    hoy = timezone.now().date()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    inicio_mes = hoy.replace(day=1)

    # Estadísticas generales
    total_clientes = Cliente.objects.filter(negocio=negocio, esta_activo=True).count()
    total_servicios = Servicio.objects.filter(negocio=negocio, esta_activo=True).count()

    # Citas de hoy
    citas_hoy = Cita.objects.filter(
        negocio=negocio,
        fecha_hora__date=hoy
    ).order_by('fecha_hora')

    # Citas pendientes de confirmar abono
    citas_pendientes_abono = Cita.objects.filter(
        negocio=negocio,
        estado='pendiente_abono'
    ).count()

    # Citas de la semana
    citas_semana = Cita.objects.filter(
        negocio=negocio,
        fecha_hora__date__gte=inicio_semana,
        fecha_hora__date__lte=hoy + timedelta(days=7)
    ).order_by('fecha_hora')[:10]

    # Ingresos del mes (de citas completadas)
    ingresos_mes = Cita.objects.filter(
        negocio=negocio,
        estado='completada',
        fecha_hora__date__gte=inicio_mes
    ).aggregate(
        total=Sum('servicio__precio')
    )['total'] or 0

    # Abonos pendientes de confirmar
    abonos_pendientes = Abono.objects.filter(
        cita__negocio=negocio,
        estado='pendiente'
    ).order_by('-fecha_creacion')[:5]

    # Clientes nuevos del mes
    clientes_nuevos_mes = Cliente.objects.filter(
        negocio=negocio,
        fecha_registro__gte=inicio_mes
    ).count()

    context = {
        'negocio': negocio,
        'seccion_activa': 'dashboard',
        'total_clientes': total_clientes,
        'total_servicios': total_servicios,
        'citas_hoy': citas_hoy,
        'citas_pendientes_abono': citas_pendientes_abono,
        'citas_semana': citas_semana,
        'ingresos_mes': ingresos_mes,
        'abonos_pendientes': abonos_pendientes,
        'clientes_nuevos_mes': clientes_nuevos_mes,
        'hoy': hoy,
    }

    return render(request, 'admin_panel/dashboard.html', context)


@admin_required
def servicios_admin(request, slug):
    """
    Gestión de servicios del negocio
    """
    negocio = get_object_or_404(Negocio, slug=slug)
    servicios = Servicio.objects.filter(negocio=negocio).order_by('orden', 'nombre')

    context = {
        'negocio': negocio,
        'seccion_activa': 'servicios',
        'servicios': servicios,
    }

    return render(request, 'admin_panel/servicios.html', context)


@admin_required
def agenda_admin(request, slug):
    """
    Agenda de citas del negocio
    """
    negocio = get_object_or_404(Negocio, slug=slug)

    # Filtrar por fecha si se proporciona
    fecha_str = request.GET.get('fecha')
    if fecha_str:
        try:
            from datetime import datetime
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            fecha = timezone.now().date()
    else:
        fecha = timezone.now().date()

    # Obtener citas del día
    citas = Cita.objects.filter(
        negocio=negocio,
        fecha_hora__date=fecha
    ).select_related('cliente', 'servicio').order_by('fecha_hora')

    # Estadísticas del día
    stats = {
        'total': citas.count(),
        'confirmadas': citas.filter(estado='confirmada').count(),
        'pendientes': citas.filter(estado='pendiente_abono').count(),
        'completadas': citas.filter(estado='completada').count(),
        'canceladas': citas.filter(estado='cancelada').count(),
    }

    context = {
        'negocio': negocio,
        'seccion_activa': 'agenda',
        'citas': citas,
        'fecha': fecha,
        'stats': stats,
    }

    return render(request, 'admin_panel/agenda.html', context)


@admin_required
def clientes_admin(request, slug):
    """
    Gestión de clientes del negocio
    """
    negocio = get_object_or_404(Negocio, slug=slug)

    # Búsqueda
    q = request.GET.get('q', '')
    clientes = Cliente.objects.filter(negocio=negocio)

    if q:
        clientes = clientes.filter(
            Q(nombre__icontains=q) |
            Q(telefono__icontains=q) |
            Q(email__icontains=q)
        )

    clientes = clientes.order_by('-fecha_registro')

    context = {
        'negocio': negocio,
        'seccion_activa': 'clientes',
        'clientes': clientes,
        'q': q,
    }

    return render(request, 'admin_panel/clientes.html', context)


@admin_required
def abonos_admin(request, slug):
    """
    Gestión de abonos pendientes
    """
    negocio = get_object_or_404(Negocio, slug=slug)

    # Filtrar por estado
    estado = request.GET.get('estado', 'pendiente')

    abonos = Abono.objects.filter(
        cita__negocio=negocio
    ).select_related('cita__cliente', 'cita__servicio')

    if estado and estado != 'todos':
        abonos = abonos.filter(estado=estado)

    abonos = abonos.order_by('-fecha_creacion')

    context = {
        'negocio': negocio,
        'seccion_activa': 'abonos',
        'abonos': abonos,
        'estado_filtro': estado,
    }

    return render(request, 'admin_panel/abonos.html', context)


@admin_required
def configuracion_admin(request, slug):
    """
    Configuración del negocio
    """
    negocio = get_object_or_404(Negocio, slug=slug)

    context = {
        'negocio': negocio,
        'seccion_activa': 'configuracion',
    }

    return render(request, 'admin_panel/configuracion.html', context)
