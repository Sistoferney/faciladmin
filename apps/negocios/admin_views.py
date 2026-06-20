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
from .models import Negocio, BloqueoAgenda
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
    Agenda de citas del negocio - Vista de calendario semanal
    """
    negocio = get_object_or_404(Negocio, slug=slug)
    from datetime import datetime, time, timedelta

    # Obtener fecha de referencia (por defecto hoy)
    fecha_str = request.GET.get('fecha')
    if fecha_str:
        try:
            fecha_referencia = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            fecha_referencia = timezone.now().date()
    else:
        fecha_referencia = timezone.now().date()

    # Calcular inicio de la semana (lunes)
    dias_desde_lunes = fecha_referencia.weekday()
    inicio_semana = fecha_referencia - timedelta(days=dias_desde_lunes)

    # Generar los 7 días de la semana
    dias_semana = []
    for i in range(7):
        dia = inicio_semana + timedelta(days=i)
        dias_semana.append({
            'fecha': dia,
            'nombre': ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'][i],
            'es_hoy': dia == timezone.now().date()
        })

    # Generar bloques de tiempo de 30 minutos
    hora_inicio = negocio.horario_apertura or time(8, 0)
    hora_fin = negocio.horario_cierre or time(20, 0)

    bloques_tiempo = []
    hora_actual = datetime.combine(fecha_referencia, hora_inicio)
    # Extender 2 horas después del cierre para mostrar citas que se extienden
    hora_final = datetime.combine(fecha_referencia, hora_fin) + timedelta(hours=2)

    while hora_actual < hora_final:
        bloques_tiempo.append({
            'hora': hora_actual.time(),
            'hora_str': hora_actual.strftime('%H:%M'),
            'fuera_de_horario': hora_actual.time() >= hora_fin  # Marcar slots fuera de horario
        })
        hora_actual += timedelta(minutes=30)

    # Obtener todas las citas de la semana
    fecha_inicio_semana = datetime.combine(inicio_semana, time.min)
    fecha_fin_semana = datetime.combine(inicio_semana + timedelta(days=6), time.max)

    citas_semana = Cita.objects.filter(
        negocio=negocio,
        fecha_hora__gte=fecha_inicio_semana,
        fecha_hora__lte=fecha_fin_semana
    ).select_related('cliente', 'servicio').order_by('fecha_hora')

    # Obtener bloqueos de la semana
    bloqueos_semana = BloqueoAgenda.objects.filter(
        negocio=negocio,
        esta_activo=True,
        fecha_inicio__lte=fecha_fin_semana,
        fecha_fin__gte=fecha_inicio_semana
    ).order_by('fecha_inicio')

    # Crear una matriz para mapear citas y bloqueos a cada celda del calendario
    calendario_grid = {}

    # Mapear citas y marcar todos los slots que ocupan
    for cita in citas_semana:
        # Calcular cuántos slots de 30 minutos ocupa esta cita
        duracion_minutos = cita.duracion_minutos
        num_slots = (duracion_minutos + 29) // 30  # Redondear hacia arriba

        # Datos serializables de la cita
        cita_data = {
            'id': cita.id,
            'cliente': cita.cliente.nombre,
            'servicio': cita.servicio.nombre,
            'estado': cita.estado,
            'hora': cita.fecha_hora.strftime('%H:%M'),
            'duracion': duracion_minutos,
        }

        # Marcar todos los slots que ocupa esta cita
        for i in range(num_slots):
            slot_tiempo = cita.fecha_hora + timedelta(minutes=i * 30)
            dia_key = slot_tiempo.date().isoformat()
            hora_key = slot_tiempo.strftime('%H:%M')
            celda_key = f"{dia_key}_{hora_key}"

            if celda_key not in calendario_grid:
                calendario_grid[celda_key] = {'citas': [], 'bloqueado': False, 'bloqueos': []}

            # Solo agregar la cita completa en el primer slot
            # En los slots siguientes, marcar como ocupado
            if i == 0:
                calendario_grid[celda_key]['citas'].append(cita_data)
            else:
                # Marcar este slot como continuación de la cita anterior
                calendario_grid[celda_key]['citas'].append({
                    'id': cita.id,
                    'cliente': cita.cliente.nombre,
                    'servicio': f"(Continuación) {cita.servicio.nombre}",
                    'estado': cita.estado,
                    'hora': cita.fecha_hora.strftime('%H:%M'),
                    'duracion': duracion_minutos,
                    'es_continuacion': True,
                })

    # Mapear bloqueos - simplificado y corregido
    for bloqueo in bloqueos_semana:
        bloqueo_data = {
            'id': bloqueo.id,
            'motivo': bloqueo.motivo_interno,
        }

        # Convertir a timezone-aware si es necesario
        inicio_dt = bloqueo.fecha_inicio
        fin_dt = bloqueo.fecha_fin

        # Iterar por cada día que abarca el bloqueo
        dia_actual = inicio_dt.date()
        while dia_actual <= fin_dt.date():
            dia_key = dia_actual.isoformat()

            # Iterar por cada bloque de tiempo del día
            for bloque in bloques_tiempo:
                # Crear datetime para este bloque
                bloque_dt = datetime.combine(dia_actual, bloque['hora'])

                # Hacer timezone-aware si es necesario
                if timezone.is_aware(inicio_dt):
                    bloque_dt = timezone.make_aware(bloque_dt)

                # Calcular fin del bloque (30 minutos después)
                bloque_fin_dt = bloque_dt + timedelta(minutes=30)

                # Verificar si este bloque se solapa con el bloqueo
                if bloque_dt < fin_dt and bloque_fin_dt > inicio_dt:
                    celda_key = f"{dia_key}_{bloque['hora_str']}"

                    if celda_key not in calendario_grid:
                        calendario_grid[celda_key] = {'citas': [], 'bloqueado': False, 'bloqueos': []}

                    calendario_grid[celda_key]['bloqueado'] = True
                    # Evitar duplicados
                    if not any(b['id'] == bloqueo_data['id'] for b in calendario_grid[celda_key]['bloqueos']):
                        calendario_grid[celda_key]['bloqueos'].append(bloqueo_data)

            dia_actual += timedelta(days=1)

    # Estadísticas de la semana
    stats = {
        'total': citas_semana.count(),
        'confirmadas': citas_semana.filter(estado='confirmada').count(),
        'pendientes': citas_semana.filter(estado='pendiente_abono').count(),
        'completadas': citas_semana.filter(estado='completada').count(),
        'canceladas': citas_semana.filter(estado='cancelada').count(),
    }

    # Navegación de semanas
    semana_anterior = inicio_semana - timedelta(days=7)
    semana_siguiente = inicio_semana + timedelta(days=7)
    fecha_hoy = timezone.now().date()  # Siempre la fecha actual

    # Convertir calendario_grid a JSON
    import json
    calendario_grid_json = json.dumps(calendario_grid)

    context = {
        'negocio': negocio,
        'seccion_activa': 'agenda',
        'fecha_referencia': fecha_referencia,
        'fecha_hoy': fecha_hoy,
        'inicio_semana': inicio_semana,
        'semana_anterior': semana_anterior,
        'semana_siguiente': semana_siguiente,
        'dias_semana': dias_semana,
        'bloques_tiempo': bloques_tiempo,
        'calendario_grid_json': calendario_grid_json,
        'stats': stats,
    }

    return render(request, 'admin_panel/agenda_calendario.html', context)


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
    Configuración del negocio - Permite editar información, imágenes y personalización
    """
    from .forms import ConfiguracionNegocioForm

    negocio = get_object_or_404(Negocio, slug=slug)

    if request.method == 'POST':
        form = ConfiguracionNegocioForm(request.POST, request.FILES, instance=negocio)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Configuración actualizada exitosamente!')
            return redirect('public:admin_configuracion', slug=slug)
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = ConfiguracionNegocioForm(instance=negocio)

    context = {
        'negocio': negocio,
        'seccion_activa': 'configuracion',
        'form': form,
    }

    return render(request, 'admin_panel/configuracion.html', context)


@admin_required
def servicio_crear(request, slug):
    """
    Crear nuevo servicio desde el dashboard del cliente
    """
    from .forms import ServicioForm

    negocio = get_object_or_404(Negocio, slug=slug)

    if request.method == 'POST':
        form = ServicioForm(request.POST, request.FILES)
        if form.is_valid():
            servicio = form.save(commit=False)
            servicio.negocio = negocio
            try:
                servicio.save()
                messages.success(request, f'¡Servicio "{servicio.nombre}" creado exitosamente!')
                return redirect('public:admin_servicios', slug=slug)
            except Exception as e:
                # Manejar error de nombre duplicado
                if 'unique constraint' in str(e).lower() or 'duplicate key' in str(e).lower():
                    messages.error(request, f'Ya existe un servicio con el nombre "{servicio.nombre}". Por favor usa un nombre diferente.')
                else:
                    messages.error(request, f'Error al crear el servicio: {str(e)}')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = ServicioForm()

    context = {
        'negocio': negocio,
        'seccion_activa': 'servicios',
        'form': form,
        'accion': 'crear',
    }

    return render(request, 'admin_panel/servicio_form.html', context)


@admin_required
def servicio_editar(request, slug, servicio_id):
    """
    Editar servicio existente desde el dashboard del cliente
    """
    from .forms import ServicioForm

    negocio = get_object_or_404(Negocio, slug=slug)
    servicio = get_object_or_404(Servicio, id=servicio_id, negocio=negocio)

    if request.method == 'POST':
        form = ServicioForm(request.POST, request.FILES, instance=servicio)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f'¡Servicio "{servicio.nombre}" actualizado exitosamente!')
                return redirect('public:admin_servicios', slug=slug)
            except Exception as e:
                # Manejar error de nombre duplicado
                if 'unique constraint' in str(e).lower() or 'duplicate key' in str(e).lower():
                    messages.error(request, f'Ya existe otro servicio con el nombre "{form.cleaned_data.get("nombre")}". Por favor usa un nombre diferente.')
                else:
                    messages.error(request, f'Error al actualizar el servicio: {str(e)}')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = ServicioForm(instance=servicio)

    context = {
        'negocio': negocio,
        'seccion_activa': 'servicios',
        'form': form,
        'servicio': servicio,
        'accion': 'editar',
    }

    return render(request, 'admin_panel/servicio_form.html', context)


@admin_required
def servicio_eliminar(request, slug, servicio_id):
    """
    Eliminar servicio desde el dashboard del cliente
    """
    negocio = get_object_or_404(Negocio, slug=slug)
    servicio = get_object_or_404(Servicio, id=servicio_id, negocio=negocio)

    if request.method == 'POST':
        nombre = servicio.nombre
        servicio.delete()
        messages.success(request, f'Servicio "{nombre}" eliminado exitosamente.')
        return redirect('public:admin_servicios', slug=slug)

    context = {
        'negocio': negocio,
        'seccion_activa': 'servicios',
        'servicio': servicio,
    }

    return render(request, 'admin_panel/servicio_confirmar_eliminar.html', context)


# ==================== GESTIÓN DE BLOQUEOS DE AGENDA ====================

@admin_required
def bloqueos_admin(request, slug):
    """
    Listado de bloqueos de horarios
    """
    negocio = get_object_or_404(Negocio, slug=slug)

    # Obtener bloqueos futuros y actuales
    hoy = timezone.now()
    bloqueos_activos = BloqueoAgenda.objects.filter(
        negocio=negocio,
        fecha_fin__gte=hoy,
        esta_activo=True
    ).order_by('fecha_inicio')

    bloqueos_pasados = BloqueoAgenda.objects.filter(
        negocio=negocio,
        fecha_fin__lt=hoy
    ).order_by('-fecha_inicio')[:10]  # Últimos 10

    context = {
        'negocio': negocio,
        'seccion_activa': 'agenda',
        'bloqueos_activos': bloqueos_activos,
        'bloqueos_pasados': bloqueos_pasados,
    }

    return render(request, 'admin_panel/bloqueos.html', context)


@admin_required
def bloqueo_crear(request, slug):
    """
    Crear nuevo bloqueo de horario
    Acepta parámetros GET fecha_inicio y fecha_fin para pre-llenar el formulario
    """
    from .forms import BloqueoAgendaForm
    from datetime import datetime

    negocio = get_object_or_404(Negocio, slug=slug)

    if request.method == 'POST':
        form = BloqueoAgendaForm(request.POST)
        if form.is_valid():
            bloqueo = form.save(commit=False)
            bloqueo.negocio = negocio
            bloqueo.save()
            messages.success(request, '¡Bloqueo de horario creado exitosamente!')
            return redirect('public:admin_agenda', slug=slug)
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        # Pre-llenar formulario con parámetros de la URL
        initial_data = {}
        fecha_inicio_param = request.GET.get('fecha_inicio')
        fecha_fin_param = request.GET.get('fecha_fin')

        if fecha_inicio_param:
            try:
                # Formato esperado: 2024-01-15T10:00
                initial_data['fecha_inicio'] = datetime.fromisoformat(fecha_inicio_param)
            except ValueError:
                pass

        if fecha_fin_param:
            try:
                initial_data['fecha_fin'] = datetime.fromisoformat(fecha_fin_param)
            except ValueError:
                pass

        form = BloqueoAgendaForm(initial=initial_data if initial_data else None)

    context = {
        'negocio': negocio,
        'seccion_activa': 'agenda',
        'form': form,
        'accion': 'crear',
    }

    return render(request, 'admin_panel/bloqueo_form.html', context)


@admin_required
def bloqueo_editar(request, slug, bloqueo_id):
    """
    Editar bloqueo de horario existente
    """
    from .forms import BloqueoAgendaForm

    negocio = get_object_or_404(Negocio, slug=slug)
    bloqueo = get_object_or_404(BloqueoAgenda, id=bloqueo_id, negocio=negocio)

    if request.method == 'POST':
        form = BloqueoAgendaForm(request.POST, instance=bloqueo)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Bloqueo actualizado exitosamente!')
            return redirect('public:bloqueos_admin', slug=slug)
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = BloqueoAgendaForm(instance=bloqueo)

    context = {
        'negocio': negocio,
        'seccion_activa': 'agenda',
        'form': form,
        'bloqueo': bloqueo,
        'accion': 'editar',
    }

    return render(request, 'admin_panel/bloqueo_form.html', context)


@admin_required
def bloqueo_eliminar(request, slug, bloqueo_id):
    """
    Eliminar bloqueo de horario
    """
    negocio = get_object_or_404(Negocio, slug=slug)
    bloqueo = get_object_or_404(BloqueoAgenda, id=bloqueo_id, negocio=negocio)

    if request.method == 'POST':
        bloqueo.delete()
        messages.success(request, 'Bloqueo eliminado exitosamente.')
        return redirect('public:bloqueos_admin', slug=slug)

    context = {
        'negocio': negocio,
        'seccion_activa': 'agenda',
        'bloqueo': bloqueo,
    }

    return render(request, 'admin_panel/bloqueo_confirmar_eliminar.html', context)


# ==================== GESTIÓN DE ESTADOS DE CITAS ====================

@admin_required
def cita_confirmar(request, slug, cita_id):
    """
    Confirmar una cita (cambiar de pendiente_abono a confirmada)
    """
    negocio = get_object_or_404(Negocio, slug=slug)
    cita = get_object_or_404(Cita, id=cita_id, negocio=negocio)

    if request.method == 'POST':
        cita.estado = 'confirmada'
        cita.save()
        messages.success(request, f'Cita de {cita.cliente.nombre} confirmada exitosamente.')
        return redirect('public:admin_agenda', slug=slug)

    context = {
        'negocio': negocio,
        'seccion_activa': 'agenda',
        'cita': cita,
    }

    return render(request, 'admin_panel/cita_confirmar.html', context)


@admin_required
def cita_completar(request, slug, cita_id):
    """
    Marcar una cita como completada
    """
    negocio = get_object_or_404(Negocio, slug=slug)
    cita = get_object_or_404(Cita, id=cita_id, negocio=negocio)

    if request.method == 'POST':
        cita.estado = 'completada'
        cita.save()
        messages.success(request, f'Cita de {cita.cliente.nombre} marcada como completada.')
        return redirect('public:admin_agenda', slug=slug)

    context = {
        'negocio': negocio,
        'seccion_activa': 'agenda',
        'cita': cita,
    }

    return render(request, 'admin_panel/cita_completar.html', context)


@admin_required
def cita_cancelar(request, slug, cita_id):
    """
    Cancelar una cita
    """
    negocio = get_object_or_404(Negocio, slug=slug)
    cita = get_object_or_404(Cita, id=cita_id, negocio=negocio)

    if request.method == 'POST':
        motivo = request.POST.get('motivo', '')
        cita.estado = 'cancelada'
        if motivo:
            cita.notas_admin = f"Cancelada: {motivo}"
        cita.save()
        messages.success(request, f'Cita de {cita.cliente.nombre} cancelada.')
        return redirect('public:admin_agenda', slug=slug)

    context = {
        'negocio': negocio,
        'seccion_activa': 'agenda',
        'cita': cita,
    }

    return render(request, 'admin_panel/cita_cancelar.html', context)


@admin_required
def cita_no_asistio(request, slug, cita_id):
    """
    Marcar que el cliente no asistió a la cita
    """
    negocio = get_object_or_404(Negocio, slug=slug)
    cita = get_object_or_404(Cita, id=cita_id, negocio=negocio)

    if request.method == 'POST':
        cita.estado = 'no_asistio'
        cita.save()
        messages.warning(request, f'Cita de {cita.cliente.nombre} marcada como no asistió.')
        return redirect('public:admin_agenda', slug=slug)

    context = {
        'negocio': negocio,
        'seccion_activa': 'agenda',
        'cita': cita,
    }

    return render(request, 'admin_panel/cita_no_asistio.html', context)


@admin_required
def abono_confirmar(request, slug, abono_id):
    """
    Confirmar un abono pendiente
    RF-53: Confirmación manual del admin
    """
    from apps.abonos.models import Abono

    negocio = get_object_or_404(Negocio, slug=slug)
    abono = get_object_or_404(Abono, id=abono_id, cita__negocio=negocio)

    if request.method == 'POST':
        abono.estado = 'confirmado'
        abono.save()

        # Actualizar estado de la cita a confirmada
        if abono.cita.estado == 'pendiente_abono':
            abono.cita.estado = 'confirmada'
            abono.cita.save()

        messages.success(request, f'¡Abono confirmado! Cita de {abono.cita.cliente.nombre} confirmada.')
        return redirect('public:abonos_admin', slug=slug)

    context = {
        'negocio': negocio,
        'seccion_activa': 'abonos',
        'abono': abono,
    }

    return render(request, 'admin_panel/abono_confirmar.html', context)


@admin_required
def abono_rechazar(request, slug, abono_id):
    """
    Rechazar un abono pendiente
    """
    from apps.abonos.models import Abono

    negocio = get_object_or_404(Negocio, slug=slug)
    abono = get_object_or_404(Abono, id=abono_id, cita__negocio=negocio)

    if request.method == 'POST':
        motivo = request.POST.get('motivo', '')
        abono.estado = 'rechazado'
        abono.notas_admin = motivo
        abono.save()

        messages.warning(request, f'Abono rechazado. El cliente {abono.cita.cliente.nombre} será notificado.')
        return redirect('public:abonos_admin', slug=slug)

    context = {
        'negocio': negocio,
        'seccion_activa': 'abonos',
        'abono': abono,
    }

    return render(request, 'admin_panel/abono_rechazar.html', context)


# ==================== GENERACIÓN DE CÓDIGO QR ====================

@admin_required
def generar_qr(request, slug):
    """
    Genera un código QR personalizado con la URL de la mini-página del negocio
    Incluye el nombre del negocio y opcionalmente el logo en el centro
    """
    from django.http import HttpResponse
    from django.conf import settings
    import qrcode
    from io import BytesIO
    from PIL import Image, ImageDraw, ImageFont
    import requests

    negocio = get_object_or_404(Negocio, slug=slug)

    # Construir URL completa de la mini-página
    site_url = settings.SITE_URL.rstrip('/')
    minipagina_url = f"{site_url}/{negocio.slug}/"

    # Crear código QR con alta corrección de errores (permite logo en el centro)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # Alta corrección (permite hasta 30% de daño)
        box_size=10,
        border=4,
    )

    qr.add_data(minipagina_url)
    qr.make(fit=True)

    # Crear imagen del QR
    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

    # Si tiene logo, agregarlo al centro del QR
    if negocio.logo:
        try:
            # Descargar/abrir logo
            if negocio.logo.url.startswith('http'):
                logo_response = requests.get(negocio.logo.url, timeout=5)
                logo = Image.open(BytesIO(logo_response.content))
            else:
                logo = Image.open(negocio.logo.path)

            # Calcular tamaño del logo (20% del QR)
            qr_width, qr_height = qr_img.size
            logo_size = int(qr_width * 0.2)

            # Redimensionar logo manteniendo aspecto
            logo.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)

            # Crear fondo blanco para el logo (para mejor visibilidad)
            logo_bg_size = int(logo_size * 1.2)
            logo_bg = Image.new('RGB', (logo_bg_size, logo_bg_size), 'white')

            # Calcular posición centrada del logo
            logo_pos = ((logo_bg_size - logo.size[0]) // 2, (logo_bg_size - logo.size[1]) // 2)

            # Pegar logo en fondo blanco (con transparencia si existe)
            if logo.mode == 'RGBA':
                logo_bg.paste(logo, logo_pos, logo)
            else:
                logo_bg.paste(logo, logo_pos)

            # Calcular posición central en el QR
            qr_logo_pos = ((qr_width - logo_bg_size) // 2, (qr_height - logo_bg_size) // 2)

            # Pegar logo con fondo en el QR
            qr_img.paste(logo_bg, qr_logo_pos)
        except Exception as e:
            # Si falla, continuar sin logo
            print(f"Error agregando logo al QR: {e}")

    # Crear imagen final con texto
    # Agregar espacio abajo para el nombre
    final_width = qr_img.size[0] + 40  # Padding lateral
    final_height = qr_img.size[1] + 100  # Espacio para texto
    final_img = Image.new('RGB', (final_width, final_height), 'white')

    # Pegar QR centrado
    qr_pos = (20, 20)
    final_img.paste(qr_img, qr_pos)

    # Agregar nombre del negocio
    draw = ImageDraw.Draw(final_img)

    # Intentar usar fuente del sistema, si no, usar default
    try:
        font_title = ImageFont.truetype("arial.ttf", 28)
        font_url = ImageFont.truetype("arial.ttf", 16)
    except:
        font_title = ImageFont.load_default()
        font_url = ImageFont.load_default()

    # Dibujar nombre del negocio
    text = negocio.nombre
    # Calcular posición centrada
    bbox = draw.textbbox((0, 0), text, font=font_title)
    text_width = bbox[2] - bbox[0]
    text_x = (final_width - text_width) // 2
    text_y = qr_img.size[1] + 30

    draw.text((text_x, text_y), text, fill='black', font=font_title)

    # Agregar URL pequeña
    url_text = f"{negocio.slug}"
    bbox_url = draw.textbbox((0, 0), url_text, font=font_url)
    url_width = bbox_url[2] - bbox_url[0]
    url_x = (final_width - url_width) // 2
    url_y = text_y + 40

    draw.text((url_x, url_y), url_text, fill='gray', font=font_url)

    # Guardar en buffer
    buffer = BytesIO()
    final_img.save(buffer, format='PNG')
    buffer.seek(0)

    # Retornar como respuesta HTTP
    response = HttpResponse(buffer.getvalue(), content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="qr_{negocio.slug}.png"'

    return response
