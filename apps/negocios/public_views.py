"""
Vistas públicas para las mini páginas de cada negocio
RF-08 a RF-12, RF-16 a RF-19
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit
from datetime import datetime, timedelta
import re
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


@ratelimit(key='ip', rate='10/h', method='POST', block=True)
def agendar_cita(request, slug):
    """
    RF-16 a RF-19: Sistema de reservas
    Permite al cliente agendar una cita
    Rate limit: 10 reservas por hora por IP
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
            # Obtener y limpiar datos del formulario
            nombre = request.POST.get('nombre', '').strip()
            telefono = request.POST.get('telefono', '').strip()
            email = request.POST.get('email', '').strip()
            servicio_id = request.POST.get('servicio')
            fecha = request.POST.get('fecha')
            hora = request.POST.get('hora')
            notas = request.POST.get('notas', '').strip()

            # Datos de dirección para servicios a domicilio
            direccion = request.POST.get('direccion', '').strip()
            ciudad = request.POST.get('ciudad', '').strip()
            codigo_postal = request.POST.get('codigo_postal', '').strip()
            referencia_direccion = request.POST.get('referencia_direccion', '').strip()

            # Validaciones básicas
            if not all([nombre, telefono, servicio_id, fecha, hora]):
                messages.error(request, 'Por favor completa todos los campos obligatorios.')
                return redirect('public:agendar', slug=slug)

            # Validar longitud del nombre
            if len(nombre) < 2 or len(nombre) > 200:
                messages.error(request, 'El nombre debe tener entre 2 y 200 caracteres.')
                return redirect('public:agendar', slug=slug)

            # Validar formato de teléfono (números, espacios, +, -, (), mínimo 10 dígitos)
            telefono_digitos = re.sub(r'\D', '', telefono)
            if len(telefono_digitos) < 10 or len(telefono_digitos) > 15:
                messages.error(request, 'El número de teléfono debe tener entre 10 y 15 dígitos.')
                return redirect('public:agendar', slug=slug)

            # Validar email si fue proporcionado
            if email and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
                messages.error(request, 'El formato del email no es válido.')
                return redirect('public:agendar', slug=slug)

            # Validar dirección si el negocio es a domicilio
            if negocio.es_a_domicilio and not all([direccion, ciudad]):
                messages.error(request, 'Por favor completa la dirección para el servicio a domicilio.')
                return redirect('public:agendar', slug=slug)

            # Obtener servicio
            servicio = Servicio.objects.get(id=servicio_id, negocio=negocio)

            # Crear fecha_hora en la zona horaria local (Colombia)
            import pytz
            fecha_hora_naive = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
            tz = pytz.timezone('America/Bogota')
            fecha_hora = tz.localize(fecha_hora_naive)

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

            # Actualizar dirección del cliente si el negocio es a domicilio
            if negocio.es_a_domicilio:
                cliente.direccion = direccion
                cliente.ciudad = ciudad
                cliente.codigo_postal = codigo_postal
                cliente.referencia_direccion = referencia_direccion
                cliente.save()

            # Validar que no exista una cita duplicada
            citas_existentes = Cita.objects.filter(
                cliente=cliente,
                negocio=negocio,
                fecha_hora=fecha_hora,
                estado__in=['pendiente_abono', 'confirmada']
            ).exists()

            if citas_existentes:
                messages.error(request, 'Ya tienes una cita agendada en este horario. Por favor elige otro horario.')
                return redirect('public:agendar', slug=slug)

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

            # RF-49, RF-50: Crear registro de abono si el servicio lo requiere
            if servicio.requiere_pago_abono:
                from apps.abonos.models import Abono
                Abono.objects.create(
                    cita=cita,
                    monto=servicio.precio_abono,
                    metodo_pago='transferencia',  # Por defecto transferencia
                    estado='pendiente',
                    fecha_limite=cita.fecha_limite_abono
                )

            # Enviar notificación push al administrador del negocio
            try:
                from apps.notificaciones.services import NotificacionService
                service = NotificacionService()

                titulo_admin = "Nueva cita agendada"
                mensaje_admin = f"""
{cliente.nombre} ha agendado una cita:

📅 {fecha_hora.strftime('%d/%m/%Y')}
🕐 {fecha_hora.strftime('%H:%M')}
✂️ {servicio.nombre}
💰 ${servicio.precio}
📞 Tel: {cliente.telefono}
                """.strip()

                if notas:
                    mensaje_admin += f"\n\n📝 Notas: {notas}"

                service.enviar_push(
                    cliente=cliente,
                    titulo=titulo_admin,
                    mensaje=mensaje_admin,
                    cita=cita,
                    enviar_a_admin=True
                )
            except Exception as e:
                print(f"[Notificación Admin] Error al enviar notificación de nueva cita: {e}")

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


@ratelimit(key='ip', rate='60/m', block=True)
def disponibilidad_api(request, slug):
    """
    API para obtener horarios disponibles
    RF-17: Disponibilidad en tiempo real
    Rate limit: 60 consultas por minuto por IP
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

        # Verificar si el negocio trabaja en este día de la semana
        dia_semana = fecha_obj.weekday()  # 0=Lunes, 6=Domingo

        # Verificar con ConfiguracionHorario si existe
        config_dia = negocio.configuraciones_horario.filter(dia_semana=dia_semana).first()
        if config_dia:
            # Hay configuración específica para este día
            if not config_dia.esta_abierto:
                return JsonResponse({'horarios': []})  # Día cerrado, sin horarios
            # Usar horarios específicos del día
            hora_apertura = config_dia.hora_apertura
            hora_cierre = config_dia.hora_cierre
        else:
            # No hay configuración específica, usar horarios generales
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
                # Crear fecha_hora en zona horaria local (Colombia)
                import pytz
                fecha_hora_naive = datetime.combine(fecha_obj, datetime.strptime(hora_str, '%H:%M').time())
                tz = pytz.timezone('America/Bogota')
                fecha_hora = tz.localize(fecha_hora_naive)

                # Validar que sea en el futuro
                if fecha_hora <= timezone.now():
                    continue

                # Verificar si ya hay cita en ese horario (considerar duración del servicio)
                # Una cita ocupa el slot + los siguientes slots según su duración
                fin_slot = fecha_hora + timedelta(minutes=servicio.duracion_minutos)

                # VALIDACIÓN: No permitir citas que terminen después del horario de cierre
                hora_cierre_dt = datetime.combine(fecha_obj, hora_cierre)
                if timezone.is_aware(fecha_hora):
                    hora_cierre_dt = tz.localize(hora_cierre_dt)
                if fin_slot > hora_cierre_dt:
                    # La cita terminaría después del horario de cierre, no disponible
                    continue

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


@ratelimit(key='ip', rate='60/m', block=True)
def fechas_disponibles_api(request, slug):
    """
    API para obtener fechas con disponibilidad en un mes
    Retorna lista de fechas que tienen al menos un horario disponible
    Rate limit: 60 consultas por minuto por IP
    """
    import pytz

    negocio = get_object_or_404(Negocio, slug=slug, esta_activo=True)

    servicio_id = request.GET.get('servicio')
    year = request.GET.get('year')
    month = request.GET.get('month')

    if not all([servicio_id, year, month]):
        return JsonResponse({'error': 'Faltan parámetros (servicio, year, month)'}, status=400)

    try:
        servicio = Servicio.objects.get(id=servicio_id, negocio=negocio)
        year = int(year)
        month = int(month)

        # Obtener primer y último día del mes
        primer_dia = datetime(year, month, 1).date()
        if month == 12:
            ultimo_dia = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            ultimo_dia = datetime(year, month + 1, 1).date() - timedelta(days=1)

        # Obtener horarios del negocio
        hora_apertura = negocio.horario_apertura if negocio.horario_apertura else datetime.strptime('09:00', '%H:%M').time()
        hora_cierre = negocio.horario_cierre if negocio.horario_cierre else datetime.strptime('19:00', '%H:%M').time()

        fechas_con_disponibilidad = []
        fecha_actual = timezone.now().date()
        tz = pytz.timezone('America/Bogota')

        # Iterar cada día del mes
        fecha = primer_dia
        while fecha <= ultimo_dia:
            # Saltar fechas pasadas
            if fecha < fecha_actual:
                fecha += timedelta(days=1)
                continue

            # Verificar si el negocio trabaja en este día de la semana
            dia_semana = fecha.weekday()  # 0=Lunes, 6=Domingo

            # Opción 1: Verificar con ConfiguracionHorario si existe
            config_dia = negocio.configuraciones_horario.filter(dia_semana=dia_semana).first()
            if config_dia:
                # Hay configuración específica para este día
                if not config_dia.esta_abierto:
                    fecha += timedelta(days=1)
                    continue
                # Usar horarios específicos del día
                hora_apertura_dia = config_dia.hora_apertura
                hora_cierre_dia = config_dia.hora_cierre
            else:
                # No hay configuración específica, usar validación genérica
                # Por defecto, si no hay config, asumir que domingo (6) está cerrado
                # a menos que se especifique lo contrario
                hora_apertura_dia = hora_apertura
                hora_cierre_dia = hora_cierre

            # Verificar si hay al menos un horario disponible en este día
            tiene_disponibilidad = False
            hora_inicio = hora_apertura_dia.hour
            hora_fin = hora_cierre_dia.hour

            for hora in range(hora_inicio, hora_fin):
                if tiene_disponibilidad:
                    break

                for minuto in [0, 30]:
                    # No agregar el último slot si pasa del horario de cierre
                    if hora == hora_fin - 1 and minuto == 30:
                        if hora_cierre.minute == 0:
                            continue

                    hora_str = f"{hora:02d}:{minuto:02d}"
                    fecha_hora_naive = datetime.combine(fecha, datetime.strptime(hora_str, '%H:%M').time())
                    fecha_hora = tz.localize(fecha_hora_naive)

                    # Validar que sea en el futuro
                    if fecha_hora <= timezone.now():
                        continue

                    # Verificar si ya hay cita en ese horario
                    fin_slot = fecha_hora + timedelta(minutes=servicio.duracion_minutos)

                    # Validar que no termine después del cierre
                    hora_cierre_dt = datetime.combine(fecha, hora_cierre)
                    if timezone.is_aware(fecha_hora):
                        hora_cierre_dt = tz.localize(hora_cierre_dt)
                    if fin_slot > hora_cierre_dt:
                        continue

                    # Buscar citas que se traslapen
                    citas_traslapadas = Cita.objects.filter(
                        negocio=negocio,
                        estado__in=['pendiente_abono', 'confirmada']
                    ).filter(
                        fecha_hora__lt=fin_slot
                    ).filter(
                        fecha_hora__gte=fecha_hora - timedelta(minutes=120)
                    )

                    # Verificar si hay traslape real
                    disponible = True
                    for cita in citas_traslapadas:
                        cita_fin = cita.fecha_hora + timedelta(minutes=cita.duracion_minutos)
                        if not (fin_slot <= cita.fecha_hora or fecha_hora >= cita_fin):
                            disponible = False
                            break

                    if disponible:
                        tiene_disponibilidad = True
                        break

            if tiene_disponibilidad:
                fechas_con_disponibilidad.append(fecha.isoformat())

            fecha += timedelta(days=1)

        return JsonResponse({'fechas': fechas_con_disponibilidad})

    except Servicio.DoesNotExist:
        return JsonResponse({'error': 'Servicio no encontrado'}, status=404)
    except ValueError as e:
        return JsonResponse({'error': 'Parámetros inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@ratelimit(key='ip', rate='30/m', block=True)
def buscar_cliente_api(request, slug):
    """
    API para buscar un cliente/usuario por teléfono.
    Retorna los datos del cliente si existe.
    Busca comparando los últimos 10 dígitos del teléfono (número local).
    Rate limit: 30 búsquedas por minuto por IP
    """
    negocio = get_object_or_404(Negocio, slug=slug)
    telefono = request.GET.get('telefono', '').strip()

    if not telefono:
        return JsonResponse({'existe': False})

    try:
        # Normalizar teléfono: extraer solo dígitos
        import re
        telefono_digitos = re.sub(r'\D', '', telefono)

        # Si tiene menos de 10 dígitos, no buscar
        if len(telefono_digitos) < 10:
            return JsonResponse({'existe': False})

        # Buscar cliente por teléfono en este negocio
        from apps.clientes.models import Cliente

        # Obtener últimos 10 dígitos del teléfono buscado (número local sin código de país)
        ultimos_10_buscado = telefono_digitos[-10:]

        # Buscar entre todos los clientes del negocio
        clientes = Cliente.objects.filter(negocio=negocio)

        for cliente in clientes:
            # Normalizar teléfono del cliente
            tel_cliente_digitos = re.sub(r'\D', '', str(cliente.telefono))

            # Comparar de múltiples formas para mayor flexibilidad:
            # 1. Comparar exacto
            if telefono_digitos == tel_cliente_digitos:
                return JsonResponse({
                    'existe': True,
                    'nombre': cliente.nombre,
                    'email': cliente.email or '',
                    'telefono': str(cliente.telefono)
                })

            # 2. Comparar los últimos 10 dígitos (número local colombiano)
            ultimos_10_cliente = tel_cliente_digitos[-10:] if len(tel_cliente_digitos) >= 10 else tel_cliente_digitos
            if ultimos_10_buscado == ultimos_10_cliente:
                return JsonResponse({
                    'existe': True,
                    'nombre': cliente.nombre,
                    'email': cliente.email or '',
                    'telefono': str(cliente.telefono)
                })

            # 3. Comparar sin códigos de país (últimos 9-10 dígitos)
            # Esto maneja casos donde un número tiene 9 o 10 dígitos sin código
            ultimos_9_buscado = telefono_digitos[-9:]
            ultimos_9_cliente = tel_cliente_digitos[-9:] if len(tel_cliente_digitos) >= 9 else tel_cliente_digitos

            if ultimos_9_buscado == ultimos_9_cliente or tel_cliente_digitos.endswith(ultimos_10_buscado):
                return JsonResponse({
                    'existe': True,
                    'nombre': cliente.nombre,
                    'email': cliente.email or '',
                    'telefono': str(cliente.telefono)
                })

            # 4. Comparar si el número buscado termina con el número del cliente
            if telefono_digitos.endswith(tel_cliente_digitos):
                return JsonResponse({
                    'existe': True,
                    'nombre': cliente.nombre,
                    'email': cliente.email or '',
                    'telefono': str(cliente.telefono)
                })

        return JsonResponse({'existe': False})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def manifest_minipagina(request, slug):
    """
    Genera el manifest.json dinámico para la PWA de la mini-página (clientes)
    """
    negocio = get_object_or_404(Negocio, slug=slug, esta_activo=True)

    # URL base del sitio
    site_url = request.build_absolute_uri('/').rstrip('/')

    manifest = {
        "id": f"/{slug}/?pwa=cliente",  # ID único para mini-página del cliente
        "name": f"{negocio.nombre}",
        "short_name": negocio.nombre[:12] if len(negocio.nombre) > 12 else negocio.nombre,
        "description": negocio.descripcion or f"Agenda tu cita en {negocio.nombre}",
        "start_url": f"/{slug}/",
        "scope": f"/{slug}/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": negocio.color_primario or "#6366f1",
        "orientation": "portrait-primary",
        "icons": []
    }

    # Agregar iconos si el negocio tiene logo
    if negocio.logo:
        logo_url = request.build_absolute_uri(negocio.logo.url)
        # Generar múltiples tamaños (los navegadores escogen el apropiado)
        for size in [192, 512]:
            manifest["icons"].append({
                "src": logo_url,
                "sizes": f"{size}x{size}",
                "type": "image/png",
                "purpose": "any maskable"
            })
    else:
        # Si no hay logo, usar el logo de FacilAdmin como fallback
        manifest["icons"] = [
            {
                "src": f"{site_url}/static/images/faciladmin-logo.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": f"{site_url}/static/images/faciladmin-logo.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]

    return JsonResponse(manifest, content_type='application/manifest+json')


def mis_citas(request, slug):
    """
    Vista para que los clientes vean sus citas agendadas
    Requiere ingresar teléfono para identificarse
    """
    negocio = get_object_or_404(Negocio, slug=slug, esta_activo=True)

    citas = None
    cliente = None
    telefono = None

    if request.method == 'POST':
        telefono = request.POST.get('telefono', '').strip()

        # Validar que el teléfono no esté vacío
        if not telefono:
            messages.error(request, 'Por favor ingresa tu número de teléfono.')
            return redirect('public:mis_citas', slug=slug)

        # Validar formato de teléfono (mínimo 10 dígitos)
        telefono_digitos = re.sub(r'\D', '', telefono)
        if len(telefono_digitos) < 10:
            messages.error(request, 'El número de teléfono debe tener al menos 10 dígitos.')
            return redirect('public:mis_citas', slug=slug)

        # Buscar cliente por teléfono en este negocio
        try:
            cliente = Cliente.objects.get(telefono=telefono, negocio=negocio)

            # Obtener todas las citas del cliente, ordenadas por fecha (más recientes primero)
            citas = Cita.objects.filter(
                cliente=cliente,
                negocio=negocio
            ).select_related('servicio').order_by('-fecha_hora')

            # Separar citas en futuras y pasadas
            ahora = timezone.now()
            citas_futuras = []
            citas_pasadas = []

            for cita in citas:
                if cita.fecha_hora > ahora and cita.estado not in ['cancelada', 'completada', 'no_asistio']:
                    citas_futuras.append(cita)
                else:
                    citas_pasadas.append(cita)

        except Cliente.DoesNotExist:
            messages.warning(request, f'No encontramos citas asociadas al teléfono {telefono} en {negocio.nombre}.')
            return redirect('public:mis_citas', slug=slug)

    context = {
        'negocio': negocio,
        'cliente': cliente,
        'telefono': telefono,
        'citas_futuras': citas_futuras if cliente else None,
        'citas_pasadas': citas_pasadas if cliente else None,
        'title': f'Mis Citas - {negocio.nombre}',
    }

    return render(request, 'minipagina/mis_citas.html', context)


def editar_cita_cliente(request, slug, cita_id):
    """
    Permite al cliente editar su cita
    Restricción: solo si falta más de 24 horas
    """
    negocio = get_object_or_404(Negocio, slug=slug, esta_activo=True)
    cita = get_object_or_404(Cita, id=cita_id, negocio=negocio)

    # Validar que la cita no esté cancelada o completada
    if cita.estado in ['cancelada', 'completada', 'no_asistio']:
        messages.error(request, 'No puedes editar una cita cancelada o completada.')
        return redirect('public:mis_citas', slug=slug)

    # Validar que falten más de 24 horas
    ahora = timezone.now()
    tiempo_restante = cita.fecha_hora - ahora
    if tiempo_restante.total_seconds() < 24 * 3600:
        horas_restantes = int(tiempo_restante.total_seconds() / 3600)
        messages.error(request, f'Solo puedes editar citas con más de 24 horas de anticipación. Esta cita es en {horas_restantes} horas.')
        return redirect('public:mis_citas', slug=slug)

    # Obtener servicios activos del negocio
    servicios = Servicio.objects.filter(negocio=negocio, esta_activo=True).order_by('nombre')

    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            servicio_id = request.POST.get('servicio')
            fecha = request.POST.get('fecha')
            hora = request.POST.get('hora')
            notas = request.POST.get('notas', '').strip()

            # Validaciones básicas
            if not all([servicio_id, fecha, hora]):
                messages.error(request, 'Por favor completa todos los campos obligatorios.')
                return redirect('public:editar_cita_cliente', slug=slug, cita_id=cita_id)

            # Obtener servicio
            servicio = Servicio.objects.get(id=servicio_id, negocio=negocio, esta_activo=True)

            # Crear nueva fecha_hora
            import pytz
            fecha_hora_naive = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
            tz = pytz.timezone('America/Bogota')
            nueva_fecha_hora = tz.localize(fecha_hora_naive)

            # Validar que la nueva fecha sea futura y con más de 24 horas
            tiempo_hasta_nueva_fecha = nueva_fecha_hora - ahora
            if tiempo_hasta_nueva_fecha.total_seconds() < 24 * 3600:
                messages.error(request, 'La nueva fecha debe ser con al menos 24 horas de anticipación.')
                return redirect('public:editar_cita_cliente', slug=slug, cita_id=cita_id)

            # Validar que no haya otra cita en ese horario (del mismo cliente)
            citas_conflicto = Cita.objects.filter(
                cliente=cita.cliente,
                negocio=negocio,
                fecha_hora=nueva_fecha_hora,
                estado__in=['pendiente_abono', 'confirmada']
            ).exclude(id=cita.id).exists()

            if citas_conflicto:
                messages.error(request, 'Ya tienes otra cita agendada en ese horario.')
                return redirect('public:editar_cita_cliente', slug=slug, cita_id=cita_id)

            # Guardar cambios anteriores para notificación
            fecha_anterior = cita.fecha_hora
            servicio_anterior = cita.servicio

            # Actualizar la cita
            cita.servicio = servicio
            cita.fecha_hora = nueva_fecha_hora
            cita.duracion_minutos = servicio.duracion_minutos
            cita.notas_cliente = notas
            cita.save()

            # Enviar notificación al dueño del negocio
            try:
                from apps.notificaciones.services import NotificacionService
                service = NotificacionService()

                titulo_admin = "Cita modificada por cliente"
                mensaje_admin = f"""
{cita.cliente.nombre} ha modificado su cita:

ANTES:
📅 {fecha_anterior.strftime('%d/%m/%Y')}
🕐 {fecha_anterior.strftime('%H:%M')}
✂️ {servicio_anterior.nombre}

AHORA:
📅 {nueva_fecha_hora.strftime('%d/%m/%Y')}
🕐 {nueva_fecha_hora.strftime('%H:%M')}
✂️ {servicio.nombre}
💰 ${servicio.precio}
📞 Tel: {cita.cliente.telefono}
                """.strip()

                service.enviar_push(
                    cliente=cita.cliente,
                    titulo=titulo_admin,
                    mensaje=mensaje_admin,
                    cita=cita,
                    enviar_a_admin=True
                )
            except Exception as e:
                print(f"[Notificación Admin] Error al enviar notificación de edición: {e}")

            messages.success(request, f'¡Cita actualizada! Nueva fecha: {nueva_fecha_hora.strftime("%d/%m/%Y a las %H:%M")}')
            return redirect('public:mis_citas', slug=slug)

        except Servicio.DoesNotExist:
            messages.error(request, 'El servicio seleccionado no está disponible.')
        except Exception as e:
            messages.error(request, f'Error al editar la cita: {str(e)}')

    context = {
        'negocio': negocio,
        'cita': cita,
        'servicios': servicios,
        'title': f'Editar Cita - {negocio.nombre}',
    }

    return render(request, 'minipagina/editar_cita.html', context)


def cancelar_cita_cliente(request, slug, cita_id):
    """
    Permite al cliente cancelar su cita
    Restricción: solo si falta más de 2 horas
    """
    negocio = get_object_or_404(Negocio, slug=slug, esta_activo=True)
    cita = get_object_or_404(Cita, id=cita_id, negocio=negocio)

    # Validar que la cita no esté ya cancelada o completada
    if cita.estado in ['cancelada', 'completada', 'no_asistio']:
        messages.error(request, 'Esta cita ya fue cancelada o completada.')
        return redirect('public:mis_citas', slug=slug)

    # Validar que falten más de 2 horas
    ahora = timezone.now()
    tiempo_restante = cita.fecha_hora - ahora
    if tiempo_restante.total_seconds() < 2 * 3600:
        horas_restantes = max(0, int(tiempo_restante.total_seconds() / 3600))
        minutos_restantes = max(0, int((tiempo_restante.total_seconds() % 3600) / 60))
        messages.error(request, f'Solo puedes cancelar citas con más de 2 horas de anticipación. Esta cita es en {horas_restantes}h {minutos_restantes}m.')
        return redirect('public:mis_citas', slug=slug)

    if request.method == 'POST':
        # Opcional: guardar motivo de cancelación
        motivo = request.POST.get('motivo', '').strip()

        # Actualizar estado de la cita
        cita.estado = 'cancelada'
        if motivo:
            cita.notas_internas = f"Cancelada por cliente. Motivo: {motivo}"
        else:
            cita.notas_internas = "Cancelada por cliente"
        cita.save()

        # Enviar notificación al dueño del negocio
        try:
            from apps.notificaciones.services import NotificacionService
            service = NotificacionService()

            titulo_admin = "Cita cancelada por cliente"
            mensaje_admin = f"""
{cita.cliente.nombre} ha cancelado su cita:

📅 {cita.fecha_hora.strftime('%d/%m/%Y')}
🕐 {cita.fecha_hora.strftime('%H:%M')}
✂️ {cita.servicio.nombre}
📞 Tel: {cita.cliente.telefono}
            """.strip()

            if motivo:
                mensaje_admin += f"\n\n💬 Motivo: {motivo}"

            service.enviar_push(
                cliente=cita.cliente,
                titulo=titulo_admin,
                mensaje=mensaje_admin,
                cita=cita,
                enviar_a_admin=True
            )
        except Exception as e:
            print(f"[Notificación Admin] Error al enviar notificación de cancelación: {e}")

        messages.success(request, 'Tu cita ha sido cancelada exitosamente.')
        return redirect('public:mis_citas', slug=slug)

    context = {
        'negocio': negocio,
        'cita': cita,
        'title': f'Cancelar Cita - {negocio.nombre}',
    }

    return render(request, 'minipagina/cancelar_cita.html', context)


def manifest_admin(request, slug):
    """
    Genera el manifest.json dinámico para la PWA del panel admin (dueños)
    """
    negocio = get_object_or_404(Negocio, slug=slug)

    # URL base del sitio
    site_url = request.build_absolute_uri('/').rstrip('/')

    manifest = {
        "id": f"/{slug}/admin/?pwa=admin",  # ID único para panel de admin
        "name": f"{negocio.nombre} - Admin",
        "short_name": f"{negocio.nombre[:8]} Admin",
        "description": f"Panel de administración de {negocio.nombre}",
        "start_url": f"/{slug}/admin/",
        "scope": f"/{slug}/admin/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": negocio.color_primario or "#6366f1",
        "orientation": "portrait-primary",
        "icons": []
    }

    # Agregar iconos si el negocio tiene logo
    if negocio.logo:
        logo_url = request.build_absolute_uri(negocio.logo.url)
        for size in [192, 512]:
            manifest["icons"].append({
                "src": logo_url,
                "sizes": f"{size}x{size}",
                "type": "image/png",
                "purpose": "any maskable"
            })
    else:
        # Si no hay logo, usar el logo de FacilAdmin como fallback
        manifest["icons"] = [
            {
                "src": f"{site_url}/static/images/faciladmin-logo.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": f"{site_url}/static/images/faciladmin-logo.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]

    return JsonResponse(manifest, content_type='application/manifest+json')

def diagnostico_vapid_config(request):
    """
    Diagnóstico de configuración VAPID
    Muestra información básica de las VAPID keys sin exponer datos sensibles
    """
    from django.http import JsonResponse
    from django.conf import settings
    import os

    vapid_settings = settings.WEBPUSH_SETTINGS

    # Verificar si las variables están en el entorno
    env_has_public = bool(os.environ.get('VAPID_PUBLIC_KEY'))
    env_has_private = bool(os.environ.get('VAPID_PRIVATE_KEY'))
    env_has_private_b64 = bool(os.environ.get('VAPID_PRIVATE_KEY_B64'))

    return JsonResponse({
        # Variables de entorno
        'env_VAPID_PUBLIC_KEY': 'configured' if env_has_public else 'missing',
        'env_VAPID_PRIVATE_KEY': 'configured' if env_has_private else 'missing',
        'env_VAPID_PRIVATE_KEY_B64': 'configured' if env_has_private_b64 else 'missing',

        # Settings cargados
        'settings_public_key_present': bool(vapid_settings.get('VAPID_PUBLIC_KEY')),
        'settings_public_key_length': len(vapid_settings.get('VAPID_PUBLIC_KEY', '')),
        'settings_private_key_present': bool(vapid_settings.get('VAPID_PRIVATE_KEY')),
        'settings_private_key_length': len(vapid_settings.get('VAPID_PRIVATE_KEY', '')),
        'settings_private_key_format': 'PEM' if vapid_settings.get('VAPID_PRIVATE_KEY', '').startswith('-----BEGIN') else 'unknown',
        'settings_admin_email': vapid_settings.get('VAPID_ADMIN_EMAIL'),
    })


def diagnostico_push(request):
    """
    Página de diagnóstico de notificaciones push (cliente)
    Muestra el estado completo del sistema de notificaciones
    """
    from django.shortcuts import render
    return render(request, 'diagnostico_push.html')


def diagnostico_push_servidor(request):
    """
    Diagnóstico del servidor - Muestra suscripciones en la BD
    """
    from django.http import HttpResponse
    from apps.notificaciones.models import UsuarioPushSubscription, ClientePushSubscription
    from apps.negocios.models import Negocio

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Diagnóstico Servidor - Push Notifications</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }
            .container { max-width: 900px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
            h1 { color: #333; border-bottom: 3px solid #667eea; padding-bottom: 10px; }
            h2 { color: #667eea; margin-top: 30px; }
            .section { background: #f9f9f9; padding: 15px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #667eea; }
            .ok { color: #28a745; font-weight: bold; }
            .error { color: #dc3545; font-weight: bold; }
            .warning { color: #ffc107; font-weight: bold; }
            table { width: 100%; border-collapse: collapse; margin: 15px 0; }
            th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background: #667eea; color: white; }
            .code { background: #2d2d2d; color: #f8f8f2; padding: 10px; border-radius: 5px; font-family: monospace; font-size: 12px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 Diagnóstico del Servidor - Push Notifications</h1>
    """

    # 1. Suscripciones de Admin
    html += "<h2>1. Suscripciones de Administradores</h2>"
    total_admin = UsuarioPushSubscription.objects.count()
    activas_admin = UsuarioPushSubscription.objects.filter(activa=True).count()

    html += f"<div class='section'>"
    html += f"<p><strong>Total suscripciones:</strong> {total_admin}</p>"
    status_class = 'ok' if activas_admin > 0 else 'error'
    html += f"<p><strong>Suscripciones activas:</strong> <span class='{status_class}'>{activas_admin}</span></p>"

    if total_admin > 0:
        html += "<table>"
        html += "<tr><th>ID</th><th>Usuario</th><th>Negocio</th><th>Estado</th><th>Creada</th><th>Endpoint</th></tr>"
        for sub in UsuarioPushSubscription.objects.all():
            estado = "ACTIVA" if sub.activa else "INACTIVA"
            estado_class = "ok" if sub.activa else "error"
            html += f"<tr>"
            html += f"<td>{sub.id}</td>"
            html += f"<td>{sub.user.username}</td>"
            html += f"<td>{sub.negocio.nombre} ({sub.negocio.slug})</td>"
            html += f"<td class='{estado_class}'>{estado}</td>"
            html += f"<td>{sub.fecha_creacion.strftime('%Y-%m-%d %H:%M')}</td>"
            html += f"<td style='font-size: 10px;'>{sub.endpoint[:40]}...</td>"
            html += f"</tr>"
        html += "</table>"
    else:
        html += "<p class='error'>⚠️ NO HAY SUSCRIPCIONES DE ADMIN</p>"
        html += "<p>Ningún administrador se ha suscrito a las notificaciones push.</p>"

    html += "</div>"

    # 2. Suscripciones de Clientes
    html += "<h2>2. Suscripciones de Clientes</h2>"
    total_cliente = ClientePushSubscription.objects.count()
    activas_cliente = ClientePushSubscription.objects.filter(activa=True).count()

    html += f"<div class='section'>"
    html += f"<p><strong>Total suscripciones:</strong> {total_cliente}</p>"
    html += f"<p><strong>Suscripciones activas:</strong> {activas_cliente}</p>"
    html += "</div>"

    # 3. Negocios
    html += "<h2>3. Negocios</h2>"
    negocios = Negocio.objects.all()

    html += f"<div class='section'>"
    html += f"<p><strong>Total negocios:</strong> {negocios.count()}</p>"

    if negocios.exists():
        html += "<table>"
        html += "<tr><th>Negocio</th><th>Slug</th><th>Admin</th><th>Subs Admin</th></tr>"
        for negocio in negocios:
            subs_count = UsuarioPushSubscription.objects.filter(negocio=negocio, activa=True).count()
            subs_class = 'ok' if subs_count > 0 else 'error'
            html += f"<tr>"
            html += f"<td>{negocio.nombre}</td>"
            html += f"<td>{negocio.slug}</td>"
            html += f"<td>{negocio.administrador.username if negocio.administrador else 'Sin admin'}</td>"
            html += f"<td class='{subs_class}'>{subs_count}</td>"
            html += f"</tr>"
        html += "</table>"

    html += "</div>"

    # 4. Diagnóstico
    html += "<h2>4. Diagnóstico</h2>"
    html += "<div class='section'>"

    if activas_admin == 0:
        html += "<p class='error'><strong>⚠️ PROBLEMA ENCONTRADO</strong></p>"
        html += "<p>No hay suscripciones de admin activas en la base de datos.</p>"
        html += "<p><strong>Posibles causas:</strong></p>"
        html += "<ul>"
        html += "<li>El admin nunca activó las notificaciones en la PWA</li>"
        html += "<li>La API de suscripción falló al guardar</li>"
        html += "<li>Los permisos del navegador fueron bloqueados</li>"
        html += "<li>Error en el código JavaScript de suscripción</li>"
        html += "</ul>"
        html += "<p><strong>Solución:</strong></p>"
        html += "<ol>"
        html += "<li>Abre la PWA de admin ('Spa Ilusion Admin')</li>"
        html += "<li>Ve a 'Diagnóstico de Notificaciones'</li>"
        html += "<li>Verifica que 'Guardado en servidor' diga ✓ Sí</li>"
        html += "<li>Si dice ✗ No, haz clic en 'Activar Notificaciones'</li>"
        html += "</ol>"
    else:
        html += f"<p class='ok'><strong>✓ Hay {activas_admin} suscripción(es) activa(s)</strong></p>"
        html += "<p>Las notificaciones deberían estar funcionando.</p>"
        html += "<p><strong>Si no llegan las notificaciones, verifica:</strong></p>"
        html += "<ul>"
        html += "<li>Que Celery esté ejecutándose (para tareas asíncronas)</li>"
        html += "<li>Los logs cuando se crea una cita</li>"
        html += "<li>Que las VAPID keys estén configuradas correctamente</li>"
        html += "</ul>"

    html += "</div>"

    # 5. Instrucciones
    html += "<h2>5. Cómo probar</h2>"
    html += "<div class='section'>"
    html += "<p>Para probar el envío de notificaciones:</p>"
    html += "<ol>"
    html += "<li>Ve a la mini-página del negocio</li>"
    html += "<li>Agenda una nueva cita como cliente</li>"
    html += "<li>Revisa si llega la notificación al admin</li>"
    html += "<li>Revisa los logs de Railway para ver si hubo errores</li>"
    html += "</ol>"
    html += "</div>"

    html += """
        </div>
    </body>
    </html>
    """

    return HttpResponse(html)
