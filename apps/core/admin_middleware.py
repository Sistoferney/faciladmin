"""
Middleware para restringir acceso al Django Admin
Solo permite acceso a superadmins del sistema
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse


class AdminAccessMiddleware:
    """
    Middleware que bloquea el acceso al Django Admin
    para usuarios que no sean superadmin del sistema
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Verificar si la ruta es del admin de Django
        if request.path.startswith('/admin/'):
            # Permitir acceso a archivos estáticos del admin
            if request.path.startswith('/admin/jsi18n/'):
                return self.get_response(request)

            # Si el usuario no está autenticado, redirigir al login
            if not request.user.is_authenticated:
                return self.get_response(request)

            # Si el usuario NO es superadmin del sistema, bloquear acceso
            if not request.user.is_superuser:
                messages.error(
                    request,
                    'No tienes permiso para acceder al panel de administración de Django. '
                    'Esta sección está reservada solo para administradores del sistema.'
                )

                # Si tiene un negocio asociado, redirigir a su dashboard
                if hasattr(request.user, 'negocio'):
                    return redirect(f'/{request.user.negocio.slug}/admin/')
                else:
                    # Si no tiene negocio, redirigir al home
                    return redirect('/')

        response = self.get_response(request)
        return response
