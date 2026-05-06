"""
Vistas de autenticación personalizadas
"""
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required


@login_required
def redirect_after_login(request):
    """
    Redirige al usuario a su panel personalizado después del login
    """
    # Si el usuario tiene un negocio asociado, ir a su mini-página admin
    if hasattr(request.user, 'negocio'):
        return redirect(f'/{request.user.negocio.slug}/admin/')

    # Si es superadmin del sistema sin negocio, ir al admin de Django
    if request.user.is_superuser:
        return redirect('/admin/')

    # Si no tiene negocio ni es superadmin, ir al home
    return redirect('/')
