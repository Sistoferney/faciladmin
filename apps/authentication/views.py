"""
Vistas de autenticación con protección contra ataques de fuerza bruta
"""
from django.contrib.auth.views import LoginView
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Usuario, TokenRecuperacion


@method_decorator(
    ratelimit(key='ip', rate='10/5m', method='POST', block=True),
    name='dispatch'
)
class RateLimitedLoginView(LoginView):
    """
    Vista de login con protección contra fuerza bruta
    Límite: 10 intentos cada 5 minutos por dirección IP
    (Más permisivo porque ahora tenemos recuperación de contraseña)
    """
    template_name = 'registration/login.html'

    def form_invalid(self, form):
        """Mensaje personalizado cuando falla el login"""
        # Trackear intentos fallidos en la sesión
        failed_attempts = self.request.session.get('failed_login_attempts', 0) + 1
        self.request.session['failed_login_attempts'] = failed_attempts

        # Mensaje simple para los primeros 2 intentos
        if failed_attempts < 3:
            messages.error(
                self.request,
                'Usuario o contraseña incorrectos. Por favor verifica tus credenciales.'
            )
        else:
            # A partir del 3er intento, sugerir recuperación de contraseña
            # Este mensaje se marca como 'warning' para que se muestre con color especial
            messages.warning(
                self.request,
                '¿Olvidaste tu contraseña? Haz clic en el enlace de abajo para recuperarla.'
            )

        return super().form_invalid(form)

    def form_valid(self, form):
        """Limpiar contador de intentos al login exitoso"""
        self.request.session['failed_login_attempts'] = 0
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Agregar información de intentos fallidos al contexto"""
        context = super().get_context_data(**kwargs)
        context['failed_attempts'] = self.request.session.get('failed_login_attempts', 0)
        context['show_recovery_link'] = context['failed_attempts'] >= 3
        return context


@method_decorator(
    ratelimit(key='ip', rate='10/5m', method='POST', block=True),
    name='dispatch'
)
class RateLimitedTokenObtainPairView(TokenObtainPairView):
    """
    Vista de login JWT con protección contra fuerza bruta
    Límite: 10 intentos cada 5 minutos por dirección IP
    """
    pass


@method_decorator(
    ratelimit(key='ip', rate='3/h', method='POST', block=True),
    name='dispatch'
)
class SolicitarRecuperacionView(View):
    """
    Vista para solicitar recuperación de contraseña
    Límite: 3 solicitudes por hora para prevenir spam de emails
    """
    template_name = 'registration/solicitar_recuperacion.html'

    def get(self, request):
        """Muestra el formulario de solicitud"""
        return render(request, self.template_name)

    def post(self, request):
        """Procesa la solicitud de recuperación"""
        email = request.POST.get('email', '').strip().lower()

        # Validar formato básico de email
        if not email or '@' not in email:
            messages.error(request, 'Por favor ingresa un correo electrónico válido.')
            return render(request, self.template_name)

        # Siempre mostrar el mismo mensaje para no revelar si el email existe
        # (seguridad contra enumeración de usuarios)
        mensaje_exitoso = (
            'Si el correo electrónico está registrado, '
            'recibirás un enlace para restablecer tu contraseña en los próximos minutos.'
        )

        try:
            usuario = Usuario.objects.get(email=email, esta_activo=True)

            # Invalidar tokens anteriores del usuario (opcional, por seguridad)
            TokenRecuperacion.objects.filter(
                usuario=usuario,
                usado=False
            ).update(usado=True)

            # Crear nuevo token
            token = TokenRecuperacion.objects.create(
                usuario=usuario,
                ip_solicitud=self._get_client_ip(request)
            )

            # Construir URL de recuperación
            protocol = 'https' if request.is_secure() else 'http'
            domain = request.get_host()
            url_recuperacion = f"{protocol}://{domain}/recuperar-password/{token.token}/"

            # Preparar y enviar email
            contexto = {
                'usuario': usuario,
                'url_recuperacion': url_recuperacion,
                'expiracion_horas': 1,
            }

            html_message = render_to_string('emails/recuperacion_password.html', contexto)
            plain_message = strip_tags(html_message)

            send_mail(
                subject='Recuperación de contraseña - FacilAdmin',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[usuario.email],
                html_message=html_message,
                fail_silently=False,
            )

        except Usuario.DoesNotExist:
            # No hacer nada, pero mostrar el mismo mensaje
            pass
        except Exception as e:
            # Log del error pero no revelar detalles al usuario
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al enviar email de recuperación: {str(e)}")

        # Siempre mostrar mensaje de éxito
        messages.success(request, mensaje_exitoso)
        return redirect('login')

    def _get_client_ip(self, request):
        """Obtiene la IP real del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RestablecerPasswordView(View):
    """
    Vista para establecer nueva contraseña usando el token
    """
    template_name = 'registration/restablecer_password.html'

    def get(self, request, token):
        """Muestra el formulario para establecer nueva contraseña"""
        # Verificar que el token sea válido
        try:
            token_obj = TokenRecuperacion.objects.get(token=token)

            if not token_obj.es_valido():
                messages.error(
                    request,
                    'Este enlace ha expirado o ya fue utilizado. '
                    'Por favor solicita uno nuevo.'
                )
                return redirect('solicitar_recuperacion')

            return render(request, self.template_name, {'token': token})

        except TokenRecuperacion.DoesNotExist:
            messages.error(request, 'Enlace de recuperación inválido.')
            return redirect('solicitar_recuperacion')

    def post(self, request, token):
        """Procesa el cambio de contraseña"""
        try:
            token_obj = TokenRecuperacion.objects.get(token=token)

            # Verificar validez
            if not token_obj.es_valido():
                messages.error(
                    request,
                    'Este enlace ha expirado o ya fue utilizado. '
                    'Por favor solicita uno nuevo.'
                )
                return redirect('solicitar_recuperacion')

            # Obtener contraseñas del formulario
            password1 = request.POST.get('password1', '')
            password2 = request.POST.get('password2', '')

            # Validaciones
            if not password1 or not password2:
                messages.error(request, 'Por favor completa ambos campos.')
                return render(request, self.template_name, {'token': token})

            if password1 != password2:
                messages.error(request, 'Las contraseñas no coinciden.')
                return render(request, self.template_name, {'token': token})

            if len(password1) < 8:
                messages.error(request, 'La contraseña debe tener al menos 8 caracteres.')
                return render(request, self.template_name, {'token': token})

            # Cambiar la contraseña
            usuario = token_obj.usuario
            usuario.set_password(password1)
            usuario.save()

            # Marcar token como usado
            token_obj.marcar_como_usado()

            messages.success(
                request,
                'Tu contraseña ha sido restablecida exitosamente. '
                'Ahora puedes iniciar sesión con tu nueva contraseña.'
            )
            return redirect('login')

        except TokenRecuperacion.DoesNotExist:
            messages.error(request, 'Enlace de recuperación inválido.')
            return redirect('solicitar_recuperacion')
