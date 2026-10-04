"""
Vistas públicas para las mini páginas de cada negocio
RF-08 a RF-12, RF-16 a RF-19
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, Http404
from django.utils.html import escape
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit
from django.db import transaction
from datetime import datetime, timedelta
from functools import wraps
import calendar
import re
from apps.core.formato import parsear_monto, pesos
from .disponibilidad import horarios_disponibles, esta_disponible
from .models import Negocio
from apps.servicios.models import Servicio
from apps.clientes.models import Cliente
from apps.citas.models import Cita

import logging

logger = logging.getLogger(__name__)


def superuser_required(view_func):
    """
    Restringe la vista a superadmins. Para el resto responde 404
    para no revelar que el endpoint existe.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            raise Http404
        return view_func(request, *args, **kwargs)
    return wrapper


# Clave de sesión con los clientes que se han identificado en cada negocio
# Formato: {str(negocio_id): cliente_id}
SESION_CLIENTES_VERIFICADOS = 'clientes_verificados'


def _marcar_cliente_verificado(request, cliente):
    """
    Registra en la sesión que este navegador se identificó como el cliente
    (al agendar o al consultar "Mis citas" con su teléfono).
    """
    verificados = request.session.get(SESION_CLIENTES_VERIFICADOS, {})
    verificados[str(cliente.negocio_id)] = cliente.id
    request.session[SESION_CLIENTES_VERIFICADOS] = verificados


def _cliente_verificado(request, negocio):
    """Cliente identificado en esta sesión para el negocio, o None"""
    cliente_id = request.session.get(SESION_CLIENTES_VERIFICADOS, {}).get(str(negocio.id))
    if not cliente_id:
        return None
    return Cliente.objects.filter(id=cliente_id, negocio=negocio).first()


def _olvidar_cliente(request, negocio):
    """Deja de recordar al cliente de este negocio en la sesión"""
    verificados = request.session.get(SESION_CLIENTES_VERIFICADOS, {})
    if verificados.pop(str(negocio.id), None) is not None:
        request.session[SESION_CLIENTES_VERIFICADOS] = verificados


def _aviso_cita_hoy(citas_futuras):
    """'Tu cita de Masaje es hoy a las 3:00 p. m.' para la primera cita de hoy, o None"""
    from apps.notificaciones.textos_push import a_la_hora
    hoy = timezone.localdate()
    for cita in sorted(citas_futuras or [], key=lambda c: c.fecha_hora):
        if timezone.localtime(cita.fecha_hora).date() == hoy:
            return f'Tu cita de {cita.servicio.nombre} es hoy {a_la_hora(cita.fecha_hora)}.'
    return None


def _cliente_puede_gestionar(request, cita):
    """
    Verifica que la cita pertenezca al cliente identificado en esta sesión.
    Evita que se vean, editen o cancelen citas ajenas cambiando el ID en la URL.
    """
    verificados = request.session.get(SESION_CLIENTES_VERIFICADOS, {})
    return verificados.get(str(cita.negocio_id)) == cita.cliente_id


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

    # Cliente reconocido en este dispositivo (agendó o se identificó antes):
    # si tiene citas, mostrar "Mis citas" junto a "Agendar Cita"
    cliente = _cliente_verificado(request, negocio)
    tiene_citas = bool(cliente) and Cita.objects.filter(cliente=cliente, negocio=negocio).exists()
    citas_proximas = Cita.objects.filter(
        cliente=cliente,
        negocio=negocio,
        fecha_hora__gte=timezone.now(),
        estado__in=['pendiente_abono', 'confirmada'],
    ).count() if tiene_citas else 0

    context = {
        'negocio': negocio,
        'servicios': servicios,
        'tiene_citas': tiene_citas,
        'citas_proximas': citas_proximas,
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
            if not all([telefono, servicio_id, fecha, hora]):
                messages.error(request, 'Por favor completa todos los campos obligatorios.')
                return redirect('public:agendar', slug=slug)

            # El nombre solo es obligatorio para clientes nuevos: a los existentes
            # el formulario no les muestra sus datos (ver buscar_cliente_api)
            cliente_existente = Cliente.buscar_por_telefono(negocio, telefono)

            # Validar longitud del nombre
            if not cliente_existente and (len(nombre) < 2 or len(nombre) > 200):
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
            servicio = Servicio.objects.get(id=servicio_id, negocio=negocio, esta_activo=True)

            # Crear fecha_hora en la zona horaria local (Colombia)
            try:
                fecha_hora = timezone.make_aware(
                    datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
                )
            except ValueError:
                messages.error(request, 'La fecha u hora seleccionada no es válida.')
                return redirect('public:agendar', slug=slug)

            with transaction.atomic():
                # Bloquear el negocio mientras se agenda: evita que dos personas
                # reserven el mismo horario al mismo tiempo
                Negocio.objects.select_for_update().get(pk=negocio.pk)

                # Validar en el servidor lo mismo que muestra el calendario:
                # horario de atención, bloqueos y citas que se cruzan
                if not esta_disponible(negocio, fecha_hora, servicio.duracion_minutos):
                    messages.error(request, 'El horario seleccionado ya no está disponible. Por favor elige otro.')
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

                # Si estaba dado de baja y vuelve a agendar por su cuenta, se reactiva
                if not cliente.esta_activo:
                    cliente.reactivar()

                # Clientes de confianza (el dueño marcó "no exigir abono"):
                # la cita queda confirmada sin pedir anticipo
                exige_abono = servicio.requiere_pago_abono and not cliente.no_exigir_abono

                # Crear la cita
                cita = Cita.objects.create(
                    negocio=negocio,
                    cliente=cliente,
                    servicio=servicio,
                    fecha_hora=fecha_hora,
                    duracion_minutos=servicio.duracion_minutos,
                    estado='pendiente_abono' if exige_abono else 'confirmada',
                    origen='web',
                    notas_cliente=notas
                )

                # RF-49, RF-50: Crear registro de abono si el servicio lo requiere
                if exige_abono:
                    from apps.abonos.models import Abono
                    Abono.objects.create(
                        cita=cita,
                        monto=servicio.precio_abono,
                        metodo_pago='transferencia',  # Por defecto transferencia
                        estado='pendiente',
                        fecha_limite=cita.fecha_limite_abono
                    )

            # Permitir que este navegador vea/gestione la cita recién creada
            _marcar_cliente_verificado(request, cliente)

            # NOTA: La notificación al admin se envía automáticamente desde la señal post_save
            # en apps/citas/signals.py → enviar_confirmacion_cita()
            # No duplicar la llamada aquí

            # Mensaje de éxito
            if exige_abono:
                messages.success(
                    request,
                    f'¡Cita agendada! Te hemos enviado la información de pago a {telefono}. '
                    f'Por favor realiza el abono antes del {timezone.localtime(cita.fecha_limite_abono).strftime("%d/%m/%Y")}.'
                )
            else:
                messages.success(
                    request,
                    f'¡Cita confirmada! Nos vemos el {timezone.localtime(fecha_hora).strftime("%d/%m/%Y a las %H:%M")}. '
                    f'Te enviaremos un recordatorio.'
                )

            return redirect('public:confirmacion_cita', slug=slug, cita_id=cita.id)

        except Servicio.DoesNotExist:
            messages.error(request, 'El servicio seleccionado no está disponible.')
        except Exception:
            logger.exception('Error al agendar cita en %s', slug)
            messages.error(request, 'No pudimos agendar tu cita. Por favor intenta de nuevo.')

    # Si el cliente ya se identificó en este dispositivo, precargar su teléfono
    cliente_recordado = _cliente_verificado(request, negocio)

    context = {
        'negocio': negocio,
        'servicios': servicios,
        'telefono_recordado': cliente_recordado.telefono.as_e164 if cliente_recordado else '',
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

    if not _cliente_puede_gestionar(request, cita):
        messages.info(request, 'Ingresa tu número de teléfono para ver tus citas.')
        return redirect('public:mis_citas', slug=slug)

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
    negocio = get_object_or_404(Negocio, slug=slug, esta_activo=True)

    fecha = request.GET.get('fecha')
    servicio_id = request.GET.get('servicio')

    if not fecha or not servicio_id:
        return JsonResponse({'error': 'Faltan parámetros'}, status=400)

    try:
        servicio = Servicio.objects.get(id=servicio_id, negocio=negocio)
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
    except (Servicio.DoesNotExist, ValueError):
        return JsonResponse({'error': 'Parámetros inválidos'}, status=400)

    # Al editar una cita, su propio horario no debe contar como ocupado.
    # Solo se acepta si la cita es del cliente identificado en esta sesión.
    excluir_cita_id = None
    cita_id = request.GET.get('cita')
    if cita_id and cita_id.isdigit():
        cita = Cita.objects.filter(id=cita_id, negocio=negocio).first()
        if cita and _cliente_puede_gestionar(request, cita):
            excluir_cita_id = cita.id

    horarios = horarios_disponibles(
        negocio, fecha_obj, servicio.duracion_minutos, excluir_cita_id=excluir_cita_id
    )
    return JsonResponse({'horarios': horarios})


@ratelimit(key='ip', rate='60/m', block=True)
def fechas_disponibles_api(request, slug):
    """
    API para obtener fechas con disponibilidad en un mes
    Retorna lista de fechas que tienen al menos un horario disponible
    Rate limit: 60 consultas por minuto por IP
    """
    negocio = get_object_or_404(Negocio, slug=slug, esta_activo=True)

    servicio_id = request.GET.get('servicio')
    year = request.GET.get('year')
    month = request.GET.get('month')

    if not all([servicio_id, year, month]):
        return JsonResponse({'error': 'Faltan parámetros (servicio, year, month)'}, status=400)

    try:
        servicio = Servicio.objects.get(id=servicio_id, negocio=negocio)
        primer_dia = datetime(int(year), int(month), 1).date()
    except (Servicio.DoesNotExist, ValueError):
        return JsonResponse({'error': 'Parámetros inválidos'}, status=400)

    _, dias_mes = calendar.monthrange(primer_dia.year, primer_dia.month)
    hoy = timezone.localdate()

    fechas_con_disponibilidad = []
    for dia in range(dias_mes):
        fecha = primer_dia + timedelta(days=dia)
        if fecha < hoy:
            continue
        if horarios_disponibles(negocio, fecha, servicio.duracion_minutos):
            fechas_con_disponibilidad.append(fecha.isoformat())

    return JsonResponse({'fechas': fechas_con_disponibilidad})


@ratelimit(key='ip', rate='30/m', block=True)
def buscar_cliente_api(request, slug):
    """
    API para saber si un teléfono ya corresponde a un cliente del negocio.
    Solo devuelve el primer nombre para saludarlo: no expone email ni datos
    personales, ya que cualquiera puede consultar cualquier número.
    Usa la misma normalización del teléfono que al agendar (formato E.164).
    Rate limit: 30 búsquedas por minuto por IP
    """
    negocio = get_object_or_404(Negocio, slug=slug)
    telefono = request.GET.get('telefono', '').strip()

    if len(re.sub(r'\D', '', telefono)) < 10:
        return JsonResponse({'existe': False})

    cliente = Cliente.buscar_por_telefono(negocio, telefono)
    if not cliente:
        return JsonResponse({'existe': False})

    return JsonResponse({
        'existe': True,
        'nombre': cliente.nombre.split()[0] if cliente.nombre else '',
    })


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
    Vista para que los clientes vean sus citas agendadas.
    La primera vez se identifican con su teléfono; después la sesión los
    recuerda (60 días), así la PWA instalada no vuelve a pedirlo.
    """
    negocio = get_object_or_404(Negocio, slug=slug, esta_activo=True)

    if request.method == 'POST':
        # "Buscar con otro teléfono": olvidar al cliente de esta sesión
        if request.POST.get('accion') == 'salir':
            _olvidar_cliente(request, negocio)
            return redirect('public:mis_citas', slug=slug)

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

        cliente = Cliente.buscar_por_telefono(negocio, telefono)
        if not cliente:
            messages.warning(request, f'No encontramos citas asociadas al teléfono {telefono} en {negocio.nombre}.')
            return redirect('public:mis_citas', slug=slug)

        _marcar_cliente_verificado(request, cliente)
        # Redirigir (PRG): recargar la página no reenvía el formulario
        return redirect('public:mis_citas', slug=slug)

    cliente = _cliente_verificado(request, negocio)
    citas_futuras = citas_pasadas = None

    if cliente:
        citas = Cita.objects.filter(
            cliente=cliente,
            negocio=negocio
        ).select_related('servicio', 'abono').order_by('-fecha_hora')

        # Separar citas en futuras y pasadas
        ahora = timezone.now()
        citas_futuras = []
        citas_pasadas = []
        for cita in citas:
            if cita.fecha_hora > ahora and cita.estado not in ['cancelada', 'completada', 'no_asistio']:
                citas_futuras.append(cita)
            else:
                citas_pasadas.append(cita)

    context = {
        'negocio': negocio,
        'cliente': cliente,
        'telefono': cliente.telefono if cliente else None,
        'citas_futuras': citas_futuras,
        'citas_pasadas': citas_pasadas,
        # Aviso destacado si tiene una cita hoy (respaldo del recordatorio de 2 horas)
        'aviso_cita_hoy': _aviso_cita_hoy(citas_futuras),
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

    if not _cliente_puede_gestionar(request, cita):
        messages.error(request, 'Ingresa tu número de teléfono para gestionar tus citas.')
        return redirect('public:mis_citas', slug=slug)

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

            # Crear nueva fecha_hora en la zona horaria local (Colombia)
            try:
                nueva_fecha_hora = timezone.make_aware(
                    datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
                )
            except ValueError:
                messages.error(request, 'La fecha u hora seleccionada no es válida.')
                return redirect('public:editar_cita_cliente', slug=slug, cita_id=cita_id)

            # Validar que la nueva fecha sea futura y con más de 24 horas
            tiempo_hasta_nueva_fecha = nueva_fecha_hora - ahora
            if tiempo_hasta_nueva_fecha.total_seconds() < 24 * 3600:
                messages.error(request, 'La nueva fecha debe ser con al menos 24 horas de anticipación.')
                return redirect('public:editar_cita_cliente', slug=slug, cita_id=cita_id)


            with transaction.atomic():
                # Bloquear el negocio para evitar reservas simultáneas del mismo horario
                Negocio.objects.select_for_update().get(pk=negocio.pk)

                # Horario de atención, bloqueos y cruces con otras citas
                # (excluyendo esta misma cita, que se está moviendo)
                if not esta_disponible(negocio, nueva_fecha_hora, servicio.duracion_minutos,
                                       excluir_cita_id=cita.id):
                    messages.error(request, 'El horario seleccionado no está disponible. Por favor elige otro.')
                    return redirect('public:editar_cita_cliente', slug=slug, cita_id=cita_id)

                # Actualizar la cita
                cita.servicio = servicio
                cita.fecha_hora = nueva_fecha_hora
                cita.duracion_minutos = servicio.duracion_minutos
                cita.notas_cliente = notas
                cita.save()

                # Bandeja del dueño
                from apps.notificaciones import pendientes
                pendientes.abrir(cita, 'cita_modificada')

            # Enviar notificación al dueño del negocio
            try:
                from apps.notificaciones.services import NotificacionService
                service = NotificacionService()

                # Aviso corto (Chrome oculta como spam los textos largos con emojis/teléfonos)
                from apps.notificaciones.textos_push import push_dueno_cita_modificada
                titulo_admin, mensaje_admin = push_dueno_cita_modificada(cita)

                service.enviar_push(
                    cliente=cita.cliente,
                    titulo=titulo_admin,
                    mensaje=mensaje_admin,
                    cita=cita,
                    enviar_a_admin=True
                )
            except Exception:
                logger.exception('Error al notificar edición de cita %s', cita.id)

            messages.success(request, f'¡Cita actualizada! Nueva fecha: {timezone.localtime(nueva_fecha_hora).strftime("%d/%m/%Y a las %H:%M")}')
            return redirect('public:mis_citas', slug=slug)

        except Servicio.DoesNotExist:
            messages.error(request, 'El servicio seleccionado no está disponible.')
        except Exception:
            logger.exception('Error al editar cita %s', cita_id)
            messages.error(request, 'No pudimos actualizar tu cita. Por favor intenta de nuevo.')

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

    if not _cliente_puede_gestionar(request, cita):
        messages.error(request, 'Ingresa tu número de teléfono para gestionar tus citas.')
        return redirect('public:mis_citas', slug=slug)

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

        # Bandeja del dueño (la señal ya cerró los demás pendientes de la cita)
        from apps.notificaciones import pendientes
        pendientes.abrir(cita, 'cita_cancelada', f'Motivo: {motivo[:150]}' if motivo else '')

        # Enviar notificación al dueño del negocio
        try:
            from apps.notificaciones.services import NotificacionService
            service = NotificacionService()

            # Aviso corto (Chrome oculta como spam los textos largos con emojis/teléfonos)
            from apps.notificaciones.textos_push import push_dueno_cita_cancelada
            titulo_admin, mensaje_admin = push_dueno_cita_cancelada(cita)
            if motivo:
                mensaje_admin += f' · Motivo: {motivo[:80]}'

            service.enviar_push(
                cliente=cita.cliente,
                titulo=titulo_admin,
                mensaje=mensaje_admin,
                cita=cita,
                enviar_a_admin=True
            )
        except Exception:
            logger.exception('Error al notificar cancelación de cita %s', cita.id)

        messages.success(request, 'Tu cita ha sido cancelada exitosamente.')
        return redirect('public:mis_citas', slug=slug)

    context = {
        'negocio': negocio,
        'cita': cita,
        'title': f'Cancelar Cita - {negocio.nombre}',
    }

    return render(request, 'minipagina/cancelar_cita.html', context)


TAMANO_MAXIMO_COMPROBANTE = 5 * 1024 * 1024  # 5 MB (capturas de pantalla / fotos)


@ratelimit(key='ip', rate='10/h', method='POST', block=True)
@require_http_methods(["POST"])
def subir_comprobante(request, slug, cita_id):
    """
    El cliente envía la foto/captura del comprobante de su abono.
    El abono queda en "Por revisar" para el dueño, que recibe un aviso push.
    Rate limit: 10 envíos por hora por IP
    """
    from django.core.exceptions import ValidationError
    from django.forms import ImageField

    negocio = get_object_or_404(Negocio, slug=slug, esta_activo=True)
    cita = get_object_or_404(Cita, id=cita_id, negocio=negocio)

    if not _cliente_puede_gestionar(request, cita):
        messages.error(request, 'Ingresa tu número de teléfono para gestionar tus citas.')
        return redirect('public:mis_citas', slug=slug)

    abono = getattr(cita, 'abono', None)
    if abono is None or abono.estado not in ('pendiente', 'vencido', 'rechazado'):
        messages.info(request, 'Esta cita no tiene un abono pendiente.')
        return redirect('public:mis_citas', slug=slug)

    archivo = request.FILES.get('comprobante')
    if not archivo:
        messages.error(request, 'Selecciona la foto o captura de tu comprobante.')
        return redirect('public:mis_citas', slug=slug)
    if archivo.size > TAMANO_MAXIMO_COMPROBANTE:
        messages.error(request, 'La imagen es muy pesada (máximo 5 MB). Intenta con una captura de pantalla.')
        return redirect('public:mis_citas', slug=slug)
    try:
        # Verifica que sea una imagen real (Pillow), no solo por la extensión
        archivo = ImageField().clean(archivo)
    except ValidationError:
        messages.error(request, 'El archivo no es una imagen válida. Envía una foto o captura del comprobante.')
        return redirect('public:mis_citas', slug=slug)

    abono.comprobante = archivo
    abono.numero_referencia = request.POST.get('numero_referencia', '').strip()[:100]
    # Lo que dice haber pagado (puede ser más que el abono o el total);
    # el dueño lo verifica contra el comprobante al confirmar
    abono.monto_reportado = parsear_monto(request.POST.get('monto_reportado'))
    abono.fecha_pago = timezone.now()
    if abono.estado == 'rechazado':
        # Nuevo intento: vuelve a revisión del dueño
        abono.estado = 'pendiente'
    abono.save()

    # Bandeja del dueño: el pendiente de abono pasa a "comprobante enviado"
    from apps.notificaciones import pendientes
    pendientes.abrir(cita, 'abono', f'Comprobante enviado por {pesos(abono.monto_reportado or abono.monto)}')

    # Avisar al dueño (al confirmarse la transacción; si falla no afecta al cliente)
    def avisar_dueno():
        try:
            from apps.notificaciones.services import NotificacionService
            from apps.notificaciones.textos_push import push_dueno_comprobante
            titulo, mensaje = push_dueno_comprobante(cita)
            NotificacionService().enviar_push(
                cliente=cita.cliente,
                titulo=titulo,
                mensaje=mensaje,
                cita=cita,
                enviar_a_admin=True,
                url=f'/{negocio.slug}/admin/pendientes/',
            )
        except Exception:
            logger.exception('Error avisando comprobante de la cita %s', cita.id)

    transaction.on_commit(avisar_dueno)

    messages.success(request, f'¡Listo! Enviamos tu comprobante a {negocio.nombre}. Te avisaremos cuando confirmen tu pago.')
    return redirect('public:mis_citas', slug=slug)


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

@superuser_required
def diagnostico_vapid_config(request):
    """
    Diagnóstico COMPLETO de configuración VAPID
    Verifica keys, suscripciones y intenta enviar notificación de prueba
    """
    from django.http import JsonResponse, HttpResponse
    from django.conf import settings
    import os
    import json
    import traceback

    diagnostico = {
        'paso1_variables_entorno': {},
        'paso2_settings_cargados': {},
        'paso3_validacion_key': {},
        'paso4_suscripciones': {},
        'paso5_test_envio': {}
    }

    # PASO 1: Variables de entorno
    env_has_public = bool(os.environ.get('VAPID_PUBLIC_KEY'))
    env_has_private = bool(os.environ.get('VAPID_PRIVATE_KEY'))
    env_has_private_b64 = bool(os.environ.get('VAPID_PRIVATE_KEY_B64'))

    diagnostico['paso1_variables_entorno'] = {
        'VAPID_PUBLIC_KEY': 'configured' if env_has_public else 'missing',
        'VAPID_PRIVATE_KEY': 'configured' if env_has_private else 'missing',
        'VAPID_PRIVATE_KEY_B64': 'configured' if env_has_private_b64 else 'missing',
    }

    # PASO 2: Settings cargados
    vapid_settings = settings.WEBPUSH_SETTINGS
    private_key = vapid_settings.get('VAPID_PRIVATE_KEY', '')

    diagnostico['paso2_settings_cargados'] = {
        'public_key_present': bool(vapid_settings.get('VAPID_PUBLIC_KEY')),
        'public_key_length': len(vapid_settings.get('VAPID_PUBLIC_KEY', '')),
        'private_key_present': bool(private_key),
        'private_key_length': len(private_key),
        'private_key_format': 'PEM' if private_key.startswith('-----BEGIN') else 'unknown',
        'private_key_first_50_chars': private_key[:50] if private_key else '',
        'admin_email': vapid_settings.get('VAPID_ADMIN_EMAIL'),
    }

    # PASO 3: Validar que la key se puede cargar con cryptography
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend

        if private_key:
            private_key_obj = serialization.load_pem_private_key(
                private_key.encode('utf-8'),
                password=None,
                backend=default_backend()
            )
            diagnostico['paso3_validacion_key'] = {
                'status': 'OK',
                'mensaje': 'VAPID key se carga correctamente con cryptography'
            }
        else:
            diagnostico['paso3_validacion_key'] = {
                'status': 'ERROR',
                'mensaje': 'No hay VAPID private key configurada'
            }
    except Exception as e:
        diagnostico['paso3_validacion_key'] = {
            'status': 'ERROR',
            'mensaje': str(e),
            'traceback': traceback.format_exc()
        }

    # PASO 4: Verificar suscripciones
    try:
        from apps.notificaciones.models import UsuarioPushSubscription

        total_suscripciones = UsuarioPushSubscription.objects.count()
        suscripciones_activas = UsuarioPushSubscription.objects.filter(activa=True).count()

        diagnostico['paso4_suscripciones'] = {
            'total': total_suscripciones,
            'activas': suscripciones_activas,
        }

        # Mostrar detalles de una suscripción activa (si existe)
        if suscripciones_activas > 0:
            suscripcion = UsuarioPushSubscription.objects.filter(activa=True).first()
            diagnostico['paso4_suscripciones']['ejemplo'] = {
                'endpoint': suscripcion.endpoint[:50] + '...',
                'auth_length': len(suscripcion.auth),
                'p256dh_length': len(suscripcion.p256dh),
                'user': str(suscripcion.user),
                'negocio': str(suscripcion.negocio),
            }
    except Exception as e:
        diagnostico['paso4_suscripciones'] = {
            'status': 'ERROR',
            'mensaje': str(e)
        }

    # PASO 5: Intentar envío de prueba
    try:
        from apps.notificaciones.models import UsuarioPushSubscription
        from pywebpush import webpush, WebPushException

        suscripciones_activas = UsuarioPushSubscription.objects.filter(activa=True)

        if suscripciones_activas.count() > 0:
            suscripcion = suscripciones_activas.first()
            subscription_info = suscripcion.to_subscription_info()

            # Intentar enviar notificación de prueba
            try:
                # Crear objeto Vapid desde la key PEM
                # IMPORTANTE: Vapid.from_string() NO soporta formato PEM, solo RAW y DER
                from py_vapid import Vapid
                vapid = Vapid.from_pem(private_key.encode('utf-8'))

                payload = json.dumps({
                    'head': 'Test de diagnostico',
                    'body': 'Verificando configuracion VAPID',
                    'icon': '/static/images/faciladmin-logo.png',
                })

                response = webpush(
                    subscription_info=subscription_info,
                    data=payload,
                    vapid_private_key=vapid,
                    vapid_claims={
                        'sub': f"mailto:{vapid_settings.get('VAPID_ADMIN_EMAIL', 'admin@faciladmin.com')}"
                    }
                )

                diagnostico['paso5_test_envio'] = {
                    'status': 'OK',
                    'mensaje': 'Notificacion de prueba enviada exitosamente',
                    'response_status': response.status_code if hasattr(response, 'status_code') else 'unknown'
                }
            except WebPushException as e:
                diagnostico['paso5_test_envio'] = {
                    'status': 'ERROR_WEBPUSH',
                    'mensaje': str(e),
                    'response_status': e.response.status_code if hasattr(e, 'response') and e.response else 'N/A',
                    'traceback': traceback.format_exc()
                }
            except Exception as e:
                diagnostico['paso5_test_envio'] = {
                    'status': 'ERROR',
                    'mensaje': str(e),
                    'type': type(e).__name__,
                    'traceback': traceback.format_exc()
                }
        else:
            diagnostico['paso5_test_envio'] = {
                'status': 'SKIP',
                'mensaje': 'No hay suscripciones activas para probar'
            }
    except Exception as e:
        diagnostico['paso5_test_envio'] = {
            'status': 'ERROR',
            'mensaje': str(e),
            'traceback': traceback.format_exc()
        }

    # Retornar HTML formateado para mejor legibilidad
    html = "<html><head><style>body{font-family:monospace;padding:20px;}pre{background:#f5f5f5;padding:10px;border-radius:5px;}</style></head><body>"
    html += "<h1>Diagnostico VAPID - FacilAdmin</h1>"
    html += "<pre>" + escape(json.dumps(diagnostico, indent=2, ensure_ascii=False)) + "</pre>"
    html += "</body></html>"

    return HttpResponse(html)


def diagnostico_push(request):
    """
    Página de diagnóstico de notificaciones push (cliente)
    Muestra el estado completo del sistema de notificaciones
    """
    from django.shortcuts import render
    return render(request, 'diagnostico_push.html')


@superuser_required
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
            html += f"<td>{escape(sub.user.username)}</td>"
            html += f"<td>{escape(sub.negocio.nombre)} ({escape(sub.negocio.slug)})</td>"
            html += f"<td class='{estado_class}'>{estado}</td>"
            html += f"<td>{timezone.localtime(sub.fecha_creacion).strftime('%Y-%m-%d %H:%M')}</td>"
            html += f"<td style='font-size: 10px;'>{escape(sub.endpoint[:40])}...</td>"
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
            html += f"<td>{escape(negocio.nombre)}</td>"
            html += f"<td>{escape(negocio.slug)}</td>"
            html += f"<td>{escape(negocio.administrador.username) if negocio.administrador else 'Sin admin'}</td>"
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


@superuser_required
def test_enviar_push_admin(request):
    """
    Endpoint de prueba para enviar una notificación push a todos los admins suscritos
    """
    from django.http import JsonResponse
    from apps.notificaciones.models import UsuarioPushSubscription
    from pywebpush import webpush, WebPushException
    from py_vapid import Vapid
    from django.conf import settings
    from apps.notificaciones.services import OPCIONES_ENTREGA_PUSH
    import json

    # Obtener todas las suscripciones activas de administradores
    suscripciones = UsuarioPushSubscription.objects.filter(activa=True)

    if not suscripciones.exists():
        return JsonResponse({
            'success': False,
            'error': 'No hay suscripciones activas de administradores',
            'total': 0
        })

    # Preparar payload de prueba
    payload = {
        'head': 'Prueba de notificacion',
        'body': 'Si ves esto, las notificaciones push estan funcionando correctamente!',
        'icon': '/static/images/faciladmin-logo.png',
        'url': '/',
        'tag': 'test-notification',
        'requireInteraction': True,
        'vibrate': [200, 100, 200]
    }

    # Crear objeto Vapid desde la key PEM
    private_key = settings.WEBPUSH_SETTINGS.get('VAPID_PRIVATE_KEY')
    vapid = Vapid.from_pem(private_key.encode('utf-8'))

    # Enviar a todas las suscripciones
    enviados = 0
    fallidos = []

    for suscripcion in suscripciones:
        try:
            subscription_info = suscripcion.to_subscription_info()

            response = webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=vapid,
                vapid_claims={
                    'sub': f"mailto:{settings.WEBPUSH_SETTINGS.get('VAPID_ADMIN_EMAIL', 'admin@faciladmin.com')}"
                },
                **OPCIONES_ENTREGA_PUSH,
            )

            enviados += 1

        except WebPushException as e:
            # Si la suscripción expiró, marcarla como inactiva
            if e.response and e.response.status_code in [404, 410]:
                suscripcion.desactivar()
            fallidos.append({
                'id': suscripcion.id,
                'user': str(suscripcion.user),
                'error': str(e)
            })
        except Exception as e:
            fallidos.append({
                'id': suscripcion.id,
                'user': str(suscripcion.user),
                'error': str(e)
            })

    return JsonResponse({
        'success': enviados > 0,
        'total_suscripciones': suscripciones.count(),
        'enviados': enviados,
        'fallidos': len(fallidos),
        'detalles_fallidos': fallidos
    })
