from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login
from django.utils import timezone
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from datetime import timedelta
import secrets

from .models import (
    RegistroNegocio,
    Cupon,
    UsoCupon,
    PlanSuscripcion,
    Suscripcion
)
from apps.negocios.models import Negocio
from apps.authentication.models import Usuario
from apps.authentication.telefonos import filtrar_por_telefono, normalizar_telefono, telefono_registrado
from apps.core.red import ip_cliente
from django_ratelimit.decorators import ratelimit
from . import antibots

import logging
from django.db import transaction

logger = logging.getLogger(__name__)


@ratelimit(key='ip', rate='3/h', method='POST', block=False)
def registro_negocio(request):
    """
    Paso 1: Formulario de registro inicial SIMPLIFICADO (sin cupones)
    Protegido contra bots (ver antibots.py) y limitado a 3 registros por hora por IP
    """
    def mostrar():
        return render(request, 'suscripciones/registro.html', {
            'marca': antibots.marca_formulario(),
            'campo_trampa': antibots.CAMPO_TRAMPA,
            'turnstile_site_key': settings.TURNSTILE_SITE_KEY if antibots.turnstile_activo() else '',
        })

    if request.method == 'POST':
        motivo = antibots.motivo_bot(request.POST)
        if motivo:
            # Misma pantalla que a una persona: el bot no sabe qué lo delató
            logger.info('Registro descartado (bot: %s) desde %s', motivo, ip_cliente(request))
            return redirect('suscripciones:registro_pendiente')

        if getattr(request, 'limited', False):
            messages.error(request, 'Hiciste muchos intentos de registro seguidos. Intenta de nuevo en una hora.')
            return mostrar()

        if not antibots.turnstile_valido(request.POST.get('cf-turnstile-response', ''), ip_cliente(request)):
            messages.error(request, 'No pudimos verificar que no eres un robot. Por favor intenta de nuevo.')
            return mostrar()

        nombre = request.POST.get('nombre', '').strip()
        apellido = request.POST.get('apellido', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        email = request.POST.get('email', '').strip().lower()

        # Validaciones básicas
        if not all([nombre, apellido, telefono, email]):
            messages.error(request, 'Todos los campos son obligatorios')
            return mostrar()

        # Guardar el teléfono en formato único (+573001234567): así cualquier
        # variante del mismo número se reconoce como el mismo (ver telefonos.py)
        telefono_normalizado = normalizar_telefono(telefono)
        if not telefono_normalizado:
            messages.error(request, 'El número de teléfono no es válido. Ejemplo: 300 123 4567')
            return mostrar()
        telefono = telefono_normalizado

        # Por ahora el servicio es solo para Colombia (además, el bot usaba números +1)
        if not telefono.startswith('+57'):
            messages.error(request, 'Por ahora solo aceptamos números de celular de Colombia (+57).')
            return mostrar()

        if telefono_registrado(Usuario.objects.all(), telefono):
            messages.error(request, 'Este teléfono ya tiene una cuenta activa. Intenta iniciar sesión.')
            return mostrar()

        # Si ya se había registrado y no activó (enlace vencido, email mal
        # escrito o que no llegó), se actualizan sus datos y se le envía un
        # enlace nuevo, en lugar de dejar el teléfono bloqueado
        registros = filtrar_por_telefono(RegistroNegocio.objects.all(), telefono)
        registro = registros[0] if registros else None
        if registro is not None and registro.estado == 'completado':
            messages.error(request, 'Este teléfono ya está registrado. Intenta iniciar sesión.')
            return mostrar()

        es_nuevo = registro is None
        if es_nuevo:
            registro = RegistroNegocio(telefono=telefono)
        registro.nombre = nombre
        registro.apellido = apellido
        registro.email = email
        _renovar_enlace(registro)
        registro.save()

        try:
            _enviar_activacion(request, registro)
        except Exception:
            logger.exception('Error enviando email de validación a %s', email)
            if es_nuevo:
                registro.delete()
            messages.error(request, 'Hubo un error al enviar el email de validación. Por favor intenta de nuevo.')
            return mostrar()

        request.session[SESION_REGISTRO_PENDIENTE] = registro.id
        messages.success(request, f'¡Casi listo {nombre}! Te enviamos un email a {email} para activar tu cuenta.')
        return redirect('suscripciones:registro_pendiente')

    return mostrar()


# El enlace de activación dura 3 días: un día se quedaba corto para quien
# no revisa el correo a diario
HORAS_ENLACE_ACTIVACION = 72

# Registro hecho desde este navegador, para poder reenviarle el email
SESION_REGISTRO_PENDIENTE = 'registro_pendiente_id'


def _renovar_enlace(registro):
    """Token nuevo (el anterior deja de servir) con vigencia completa"""
    registro.token_validacion = secrets.token_urlsafe(32)
    registro.fecha_token_expira = timezone.now() + timedelta(hours=HORAS_ENLACE_ACTIVACION)


def _enviar_activacion(request, registro):
    """Email de activación (HTML y texto). Lanza la excepción si falla el envío."""
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string

    contexto = {
        'registro': registro,
        'enlace': request.build_absolute_uri(
            reverse('suscripciones:validar_email', kwargs={'token': registro.token_validacion})
        ),
        'horas': HORAS_ENLACE_ACTIVACION,
    }
    correo = EmailMultiAlternatives(
        subject='Activa tu cuenta de facilacces',
        body=render_to_string('emails/activar_cuenta.txt', contexto),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[registro.email],
    )
    correo.attach_alternative(render_to_string('emails/activar_cuenta.html', contexto), 'text/html')
    correo.send(fail_silently=False)


@ratelimit(key='ip', rate='3/h', method='POST', block=False)
def registro_pendiente(request):
    """
    Página que se muestra después del registro, pidiendo revisar email.
    Permite reenviar el email (máximo 3 veces por hora por IP).
    """
    registro = RegistroNegocio.objects.filter(
        id=request.session.get(SESION_REGISTRO_PENDIENTE), estado='pendiente_email',
    ).first()

    if request.method == 'POST' and registro is not None:
        if getattr(request, 'limited', False):
            messages.error(request, 'Ya reenviamos el email varias veces. Intenta de nuevo en una hora.')
        else:
            if not registro.token_valido:
                _renovar_enlace(registro)
                registro.save(update_fields=['token_validacion', 'fecha_token_expira', 'actualizado_en'])
            try:
                _enviar_activacion(request, registro)
                messages.success(request, f'Te reenviamos el email a {registro.email}.')
            except Exception:
                logger.exception('Error reenviando email de validación a %s', registro.email)
                messages.error(request, 'No pudimos reenviar el email. Por favor intenta de nuevo en unos minutos.')
        return redirect('suscripciones:registro_pendiente')

    return render(request, 'suscripciones/registro_pendiente.html', {
        'registro': registro,
        'horas_enlace': HORAS_ENLACE_ACTIVACION,
    })


def validar_email(request, token):
    """Paso 2 y 3: Validar email y completar registro en un solo paso"""
    registro = get_object_or_404(RegistroNegocio, token_validacion=token)

    # Verificar si el token es válido
    if not registro.token_valido:
        messages.error(request, 'El enlace venció. Regístrate de nuevo con el mismo teléfono y te enviaremos uno nuevo.')
        return redirect('suscripciones:registro_negocio')

    # Verificar si ya fue completado
    if registro.estado == 'completado':
        messages.info(request, 'Esta cuenta ya fue activada. Puedes iniciar sesión.')
        return redirect('login')

    # Si es POST, procesar la activación
    if request.method == 'POST':
        nombre_negocio = request.POST.get('nombre_negocio', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')

        # Validaciones
        if not nombre_negocio:
            messages.error(request, 'El nombre del negocio es obligatorio')
            return render(request, 'suscripciones/activar_cuenta.html', {'registro': registro})

        if password != password_confirm:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'suscripciones/activar_cuenta.html', {'registro': registro})

        if len(password) < 8:
            messages.error(request, 'La contraseña debe tener al menos 8 caracteres')
            return render(request, 'suscripciones/activar_cuenta.html', {'registro': registro})

        # Verificar si el usuario ya existe (por teléfono, que es el identificador único)
        if telefono_registrado(Usuario.objects.all(), registro.telefono):
            messages.error(
                request,
                'Este teléfono ya tiene una cuenta activa. '
                'Si olvidaste tu contraseña, usa la opción de recuperación en el login.'
            )
            return render(request, 'suscripciones/activar_cuenta.html', {'registro': registro})

        # Crear usuario admin
        try:
            # Todo o nada: si algo falla no queda un usuario sin negocio
            # que impida volver a intentar la activación
            with transaction.atomic():
                user = Usuario.objects.create_user(
                    telefono=registro.telefono,
                    password=password,
                    nombre=f"{registro.nombre} {registro.apellido}",
                    email=registro.email
                )

                # Crear negocio
                negocio = Negocio.objects.create(
                    nombre=nombre_negocio,
                    telefono=registro.telefono,
                    email=registro.email,
                    administrador=user,
                    esta_activo=True
                )

                # Crear suscripción trial automática
                try:
                    plan_trial = PlanSuscripcion.objects.get(tipo='trial')
                except PlanSuscripcion.DoesNotExist:
                    # Si no existe el plan, crearlo automáticamente
                    plan_trial = PlanSuscripcion.objects.create(
                        tipo='trial',
                        nombre='Trial Gratuito',
                        precio=0.00,
                        duracion_dias=120,
                        descripcion='Período de prueba gratis de 120 días',
                        activo=True,
                        push_notifications=True,
                        soporte_prioritario=False,
                    )

                # Trial siempre de 120 días
                dias_trial = 120

                suscripcion = Suscripcion.objects.create(
                    negocio=negocio,
                    plan=plan_trial,
                    estado='trial',
                    fecha_inicio=timezone.now(),
                    fecha_fin=timezone.now() + timedelta(days=dias_trial),
                    auto_renovacion=False
                )

                # Actualizar registro
                registro.estado = 'completado'
                registro.email_validado_en = timezone.now()
                registro.negocio_creado = negocio
                registro.save()

            # Login automático
            login(request, user, backend='apps.authentication.backends.TelefonoBackend')

            # Enviar email de bienvenida
            try:
                send_mail(
                    subject=f'🎉 ¡Bienvenido a facilacces, {registro.nombre}!',
                    message=f'''
Hola {registro.nombre},

¡Tu cuenta de facilacces está lista y activa!

🏢 Negocio: {nombre_negocio}
📧 Email: {registro.email}
⏰ Plan gratuito válido hasta: {timezone.localtime(suscripcion.fecha_fin).strftime('%d/%m/%Y')}

Accede a tu panel aquí: {request.build_absolute_uri('/dashboard/')}

Durante los próximos {dias_trial} días tendrás acceso COMPLETO a:
✅ Gestión ilimitada de citas
✅ Clientes y servicios ilimitados
✅ Notificaciones push
✅ Página web personalizada
✅ Código QR para reservas
✅ Soporte técnico

💡 Tip: Completa el wizard de configuración para personalizar tu negocio.

¿Preguntas? Responde este email o escríbenos a WhatsApp: +57 300 779 4375

¡Éxitos!
Equipo facilacces
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[registro.email],
                    fail_silently=True,
                )
            except:
                pass  # No fallar si el email de bienvenida falla

            messages.success(request, f'¡Bienvenido {registro.nombre}! Tu cuenta está activa por {dias_trial} días. 🎉')

            # Redirigir al dashboard
            return redirect('core:dashboard_redirect')

        except Exception:
            logger.exception('Error al activar cuenta del registro %s', registro.id)
            messages.error(request, 'Hubo un error al crear tu cuenta. Por favor contacta soporte.')
            return render(request, 'suscripciones/activar_cuenta.html', {'registro': registro})

    # GET: Mostrar formulario de activación
    context = {
        'registro': registro
    }

    return render(request, 'suscripciones/activar_cuenta.html', context)


# ===============================================
# PROGRAMA DE REFERIDOS - Vistas
# ===============================================

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import ProgramaReferidos

@login_required
def programa_referidos_dashboard(request):
    """Dashboard del programa de referidos"""
    negocio = request.user.negocios.first()
    if not negocio:
        messages.error(request, 'No tienes un negocio asociado')
        return redirect('core:dashboard_redirect')

    # Obtener o crear programa de referidos
    programa, created = ProgramaReferidos.objects.get_or_create(negocio=negocio)

    # Actualizar estado
    programa.actualizar_estado()

    # Verificar si puede generar cupón
    puede_generar, mensaje = programa.puede_generar_cupon()

    context = {
        'programa': programa,
        'puede_generar_cupon': puede_generar,
        'mensaje_cupon': mensaje,
        'referidos': [
            {
                'numero': 1,
                'negocio': programa.negocio_referido_1,
                'activo': programa.negocio_referido_1.esta_activo if programa.negocio_referido_1 else False
            },
            {
                'numero': 2,
                'negocio': programa.negocio_referido_2,
                'activo': programa.negocio_referido_2.esta_activo if programa.negocio_referido_2 else False
            },
            {
                'numero': 3,
                'negocio': programa.negocio_referido_3,
                'activo': programa.negocio_referido_3.esta_activo if programa.negocio_referido_3 else False
            }
        ]
    }

    return render(request, 'suscripciones/programa_referidos.html', context)


@login_required
def agregar_referido_ajax(request):
    """Agrega un referido mediante AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    negocio = request.user.negocios.first()
    if not negocio:
        return JsonResponse({'success': False, 'error': 'No tienes un negocio asociado'}, status=400)

    telefono = request.POST.get('telefono', '').strip()
    if not telefono:
        return JsonResponse({'success': False, 'error': 'El teléfono es obligatorio'}, status=400)

    # Obtener o crear programa
    programa, _ = ProgramaReferidos.objects.get_or_create(negocio=negocio)

    # Intentar agregar referido
    exito, mensaje = programa.agregar_referido(telefono)

    if exito:
        programa.refresh_from_db()
        return JsonResponse({
            'success': True,
            'mensaje': mensaje,
            'referidos_activos': programa.referidos_activos(),
            'cumple_requisitos': programa.cumple_requisitos()
        })
    else:
        return JsonResponse({'success': False, 'error': mensaje}, status=400)


@login_required
def generar_cupon_referidos(request):
    """Genera el cupón mensual si cumple requisitos"""
    if request.method != 'POST':
        messages.error(request, 'Método no permitido')
        return redirect('suscripciones:programa_referidos')

    negocio = request.user.negocios.first()
    if not negocio:
        messages.error(request, 'No tienes un negocio asociado')
        return redirect('core:dashboard_redirect')

    try:
        programa = ProgramaReferidos.objects.get(negocio=negocio)
    except ProgramaReferidos.DoesNotExist:
        messages.error(request, 'No estás inscrito en el programa de referidos')
        return redirect('suscripciones:programa_referidos')

    # Intentar generar cupón
    exito, mensaje, cupon = programa.generar_cupon_mensual()

    if exito:
        messages.success(request, f'¡Felicidades! {mensaje}')
        # Enviar email con el cupón
        try:
            send_mail(
                subject='🎁 Tu cupón mensual está listo - facilacces',
                message=f'''
Hola {request.user.nombre},

¡Excelente noticia! Has generado tu cupón mensual por el programa de referidos.

📋 Código del cupón: {cupon.codigo}
⏰ Válido hasta: {timezone.localtime(cupon.fecha_expiracion).strftime('%d/%m/%Y')}
🎯 Beneficio: 1 mes gratis (30 días)

Para canjear tu cupón:
1. Ingresa a tu panel de suscripciones
2. Haz clic en "Canjear cupón"
3. Ingresa el código: {cupon.codigo}

¡Gracias por recomendar facilacces!

Saludos,
El equipo de facilacces
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[request.user.email],
                fail_silently=True,
            )
        except:
            pass

    else:
        messages.warning(request, mensaje)

    return redirect('suscripciones:programa_referidos')


@login_required
def canjear_cupon(request):
    """Vista para canjear un cupón"""
    negocio = request.user.negocios.first()
    if not negocio:
        messages.error(request, 'No tienes un negocio asociado')
        return redirect('core:dashboard_redirect')

    if request.method == 'POST':
        codigo_cupon = request.POST.get('codigo_cupon', '').strip().upper()
        if not codigo_cupon:
            messages.error(request, 'Debes ingresar un código de cupón')
            return render(request, 'suscripciones/canjear_cupon.html')

        try:
            cupon = Cupon.objects.get(codigo=codigo_cupon)
        except Cupon.DoesNotExist:
            messages.error(request, f'El cupón "{codigo_cupon}" no existe')
            return render(request, 'suscripciones/canjear_cupon.html')

        # Intentar canjear
        exito, mensaje, suscripcion = cupon.canjear(negocio)

        if exito:
            messages.success(request, f'¡Perfecto! {mensaje}. Nueva fecha de vencimiento: {timezone.localtime(suscripcion.fecha_fin).strftime("%d/%m/%Y")}')
            return redirect('core:dashboard_redirect')
        else:
            messages.error(request, mensaje)

    return render(request, 'suscripciones/canjear_cupon.html')
