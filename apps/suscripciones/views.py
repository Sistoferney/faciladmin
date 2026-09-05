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


def registro_negocio(request):
    """Paso 1: Formulario de registro inicial SIMPLIFICADO (sin cupones)"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        apellido = request.POST.get('apellido', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        email = request.POST.get('email', '').strip().lower()

        # Validaciones básicas
        if not all([nombre, apellido, telefono, email]):
            messages.error(request, 'Todos los campos son obligatorios')
            return render(request, 'suscripciones/registro.html')

        # Validar que no exista
        if RegistroNegocio.objects.filter(email=email).exists():
            messages.error(request, 'Este email ya está registrado. Si ya validaste tu email, revisa tu bandeja de entrada.')
            return render(request, 'suscripciones/registro.html')

        if Usuario.objects.filter(email=email).exists():
            messages.error(request, 'Este email ya tiene una cuenta activa. Intenta iniciar sesión.')
            return render(request, 'suscripciones/registro.html')

        # Generar token de validación
        token = secrets.token_urlsafe(32)
        fecha_expira = timezone.now() + timedelta(hours=24)

        # Crear registro
        registro = RegistroNegocio.objects.create(
            nombre=nombre,
            apellido=apellido,
            email=email,
            telefono=telefono,
            token_validacion=token,
            fecha_token_expira=fecha_expira
        )

        # Enviar email de validación
        link_validacion = request.build_absolute_uri(
            reverse('suscripciones:validar_email', kwargs={'token': token})
        )

        try:
            send_mail(
                subject='✨ Activa tu cuenta gratis de 120 días - FacilAdmin',
                message=f'''
Hola {nombre},

¡Bienvenido a FacilAdmin! 🎉

Estás a un paso de acceder a tu cuenta GRATIS por 120 días con todas las funciones incluidas.

👉 Activa tu cuenta aquí:
{link_validacion}

Este enlace expira en 24 horas.

¿Qué obtienes?
✅ 120 días completamente gratis
✅ Acceso completo a todas las funciones
✅ Citas ilimitadas
✅ Notificaciones push
✅ Página web personalizada
✅ Soporte técnico

{f"🎁 BONUS: Tu cupón {codigo_cupon} te da {cupon_obj.meses_gratis} mes(es) extra!" if cupon_obj else ""}

¡Nos vemos dentro!
Equipo FacilAdmin
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

            messages.success(request, f'¡Casi listo {nombre}! Te enviamos un email a {email} para activar tu cuenta gratis.')
            return redirect('suscripciones:registro_pendiente')

        except Exception as e:
            # Si falla el email, borrar el registro y mostrar error
            registro.delete()
            messages.error(request, 'Hubo un error al enviar el email de validación. Por favor intenta de nuevo.')
            return render(request, 'suscripciones/registro.html')

    return render(request, 'suscripciones/registro.html')


def registro_pendiente(request):
    """Página que se muestra después del registro, pidiendo revisar email"""
    return render(request, 'suscripciones/registro_pendiente.html')


def validar_email(request, token):
    """Paso 2 y 3: Validar email y completar registro en un solo paso"""
    registro = get_object_or_404(RegistroNegocio, token_validacion=token)

    # Verificar si el token es válido
    if not registro.token_valido:
        messages.error(request, 'El enlace ha expirado. Solicita uno nuevo registrándote nuevamente.')
        return redirect('suscripciones:registro_negocio')

    # Verificar si ya fue completado
    if registro.estado == 'completado':
        messages.info(request, 'Esta cuenta ya fue activada. Puedes iniciar sesión.')
        return redirect('authentication:login')

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

        # Crear usuario admin
        try:
            user = Usuario.objects.create_user(
                email=registro.email,
                password=password,
                nombre=f"{registro.nombre} {registro.apellido}",
                telefono=registro.telefono
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
            plan_trial = PlanSuscripcion.objects.get(tipo='trial')

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
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            # Enviar email de bienvenida
            try:
                send_mail(
                    subject=f'🎉 ¡Bienvenido a FacilAdmin, {registro.nombre}!',
                    message=f'''
Hola {registro.nombre},

¡Tu cuenta de FacilAdmin está lista y activa!

🏢 Negocio: {nombre_negocio}
📧 Email: {registro.email}
⏰ Plan gratuito válido hasta: {suscripcion.fecha_fin.strftime('%d/%m/%Y')}

Accede a tu panel aquí: {request.build_absolute_uri('/admin/dashboard/')}

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
Equipo FacilAdmin
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[registro.email],
                    fail_silently=True,
                )
            except:
                pass  # No fallar si el email de bienvenida falla

            messages.success(request, f'¡Bienvenido {registro.nombre}! Tu cuenta está activa por {dias_trial} días. 🎉')

            # Redirigir al dashboard
            return redirect('admin_dashboard')

        except Exception as e:
            messages.error(request, f'Hubo un error al crear tu cuenta: {str(e)}. Por favor contacta soporte.')
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
        return redirect('admin_dashboard')

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
        return redirect('admin_dashboard')

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
                subject='🎁 Tu cupón mensual está listo - FacilAdmin',
                message=f'''
Hola {request.user.nombre},

¡Excelente noticia! Has generado tu cupón mensual por el programa de referidos.

📋 Código del cupón: {cupon.codigo}
⏰ Válido hasta: {cupon.fecha_expiracion.strftime('%d/%m/%Y')}
🎯 Beneficio: 1 mes gratis (30 días)

Para canjear tu cupón:
1. Ingresa a tu panel de suscripciones
2. Haz clic en "Canjear cupón"
3. Ingresa el código: {cupon.codigo}

¡Gracias por recomendar FacilAdmin!

Saludos,
El equipo de FacilAdmin
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
        return redirect('admin_dashboard')

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
            messages.success(request, f'¡Perfecto! {mensaje}. Nueva fecha de vencimiento: {suscripcion.fecha_fin.strftime("%d/%m/%Y")}')
            return redirect('admin_dashboard')
        else:
            messages.error(request, mensaje)

    return render(request, 'suscripciones/canjear_cupon.html')
