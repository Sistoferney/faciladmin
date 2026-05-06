"""
Vistas públicas para las mini páginas de cada negocio
RF-08 a RF-12, RF-16 a RF-19
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Negocio
from apps.servicios.models import Servicio
from apps.clientes.models import Cliente
from apps.citas.models import Cita


def minipagina_negocio(request, slug):
    """
    RF-09, RF-10, RF-11: Mini página pública del negocio
    Muestra información del negocio, servicios y permite agendar
    """
    negocio = get_object_or_404(Negocio, slug=slug, esta_activo=True)

    # Obtener servicios activos
    servicios = Servicio.objects.filter(
        negocio=negocio,
        esta_activo=True
    ).order_by('orden', 'nombre')

    context = {
        'negocio': negocio,
        'servicios': servicios,
        'title': f'{negocio.nombre} - Agenda tu Cita',
    }

    return render(request, 'minipagina/index.html', context)


def agendar_cita(request, slug):
    """
    RF-16 a RF-19: Sistema de reservas
    Permite al cliente agendar una cita
    """
    negocio = get_object_or_404(Negocio, slug=slug, esta_activo=True)

    if not negocio.acepta_reservas_online:
        messages.error(request, 'Este negocio no acepta reservas online en este momento.')
        return redirect('public:minipagina', slug=slug)

    # Obtener servicios activos
    servicios = Servicio.objects.filter(
        negocio=negocio,
        esta_activo=True
    ).order_by('orden', 'nombre')

    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombre = request.POST.get('nombre')
            telefono = request.POST.get('telefono')
            email = request.POST.get('email', '')
            servicio_id = request.POST.get('servicio')
            fecha = request.POST.get('fecha')
            hora = request.POST.get('hora')
            notas = request.POST.get('notas', '')

            # Validaciones básicas
            if not all([nombre, telefono, servicio_id, fecha, hora]):
                messages.error(request, 'Por favor completa todos los campos obligatorios.')
                return redirect('public:agendar', slug=slug)

            # Obtener servicio
            servicio = Servicio.objects.get(id=servicio_id, negocio=negocio)

            # Crear fecha_hora
            fecha_hora = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
            fecha_hora = timezone.make_aware(fecha_hora)

            # Validar que la fecha sea futura
            if fecha_hora < timezone.now():
                messages.error(request, 'No puedes agendar citas en el pasado.')
                return redirect('public:agendar', slug=slug)

            # RF-06, RF-24: Obtener o crear cliente por teléfono
            cliente, created = Cliente.obtener_o_crear_por_telefono(
                negocio=negocio,
                telefono=telefono,
                nombre=nombre,
                email=email
            )

            # Crear la cita
            cita = Cita.objects.create(
                negocio=negocio,
                cliente=cliente,
                servicio=servicio,
                fecha_hora=fecha_hora,
                duracion_minutos=servicio.duracion_minutos,
                estado='pendiente_abono' if servicio.requiere_pago_abono else 'confirmada',
                origen='web',
                notas_cliente=notas
            )

            # Mensaje de éxito
            if servicio.requiere_pago_abono:
                messages.success(
                    request,
                    f'¡Cita agendada! Te hemos enviado la información de pago a {telefono}. '
                    f'Por favor realiza el abono antes del {cita.fecha_limite_abono.strftime("%d/%m/%Y")}.'
                )
            else:
                messages.success(
                    request,
                    f'¡Cita confirmada! Nos vemos el {fecha_hora.strftime("%d/%m/%Y a las %H:%M")}. '
                    f'Te enviaremos un recordatorio.'
                )

            return redirect('public:confirmacion_cita', slug=slug, cita_id=cita.id)

        except Servicio.DoesNotExist:
            messages.error(request, 'El servicio seleccionado no está disponible.')
        except Exception as e:
            messages.error(request, f'Error al agendar la cita: {str(e)}')

    context = {
        'negocio': negocio,
        'servicios': servicios,
        'title': f'Agendar Cita - {negocio.nombre}',
    }

    # Usar el nuevo template con calendario visual (v2)
    return render(request, 'minipagina/agendar_v2.html', context)


def confirmacion_cita(request, slug, cita_id):
    """
    Página de confirmación después de agendar
    RF-18: Confirmación de cita
    """
    negocio = get_object_or_404(Negocio, slug=slug, esta_activo=True)
    cita = get_object_or_404(Cita, id=cita_id, negocio=negocio)

    context = {
        'negocio': negocio,
        'cita': cita,
        'title': f'Confirmación de Cita - {negocio.nombre}',
    }

    return render(request, 'minipagina/confirmacion.html', context)


def disponibilidad_api(request, slug):
    """
    API para obtener horarios disponibles
    RF-17: Disponibilidad en tiempo real
    """
    import json
    from django.http import JsonResponse

    negocio = get_object_or_404(Negocio, slug=slug, esta_activo=True)

    fecha = request.GET.get('fecha')
    servicio_id = request.GET.get('servicio')

    if not fecha or not servicio_id:
        return JsonResponse({'error': 'Faltan parámetros'}, status=400)

    try:
        servicio = Servicio.objects.get(id=servicio_id, negocio=negocio)
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()

        # Validar que la fecha no sea pasada
        if fecha_obj < timezone.now().date():
            return JsonResponse({'horarios': []})

        # Obtener horarios del negocio (usar valores por defecto si no están configurados)
        hora_apertura = negocio.horario_apertura if negocio.horario_apertura else datetime.strptime('09:00', '%H:%M').time()
        hora_cierre = negocio.horario_cierre if negocio.horario_cierre else datetime.strptime('19:00', '%H:%M').time()

        # Generar horarios disponibles cada 30 minutos
        horarios = []
        hora_inicio = hora_apertura.hour
        hora_fin = hora_cierre.hour

        for hora in range(hora_inicio, hora_fin):
            for minuto in [0, 30]:  # Slots cada 30 minutos
                # No agregar el último slot si pasa del horario de cierre
                if hora == hora_fin - 1 and minuto == 30:
                    if hora_cierre.minute == 0:
                        continue

                hora_str = f"{hora:02d}:{minuto:02d}"
                fecha_hora = timezone.make_aware(
                    datetime.combine(fecha_obj, datetime.strptime(hora_str, '%H:%M').time())
                )

                # Validar que sea en el futuro
                if fecha_hora <= timezone.now():
                    continue

                # Verificar si ya hay cita en ese horario (considerar duración del servicio)
                # Una cita ocupa el slot + los siguientes slots según su duración
                fin_slot = fecha_hora + timedelta(minutes=servicio.duracion_minutos)

                # Buscar citas que se traslapen con este slot
                citas_traslapadas = Cita.objects.filter(
                    negocio=negocio,
                    estado__in=['pendiente_abono', 'confirmada']
                ).filter(
                    fecha_hora__lt=fin_slot
                ).filter(
                    fecha_hora__gte=fecha_hora - timedelta(minutes=120)  # Verificar 2 horas antes
                )

                # Verificar si hay traslape real
                disponible = True
                for cita in citas_traslapadas:
                    cita_fin = cita.fecha_hora + timedelta(minutes=cita.duracion_minutos)
                    # Si hay traslape, no está disponible
                    if not (fin_slot <= cita.fecha_hora or fecha_hora >= cita_fin):
                        disponible = False
                        break

                if disponible:
                    horarios.append(hora_str)

        return JsonResponse({'horarios': horarios})

    except Servicio.DoesNotExist:
        return JsonResponse({'error': 'Servicio no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
