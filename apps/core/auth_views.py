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
    # Si es superadmin, ir a la landing principal
    if request.user.is_superuser:
        return redirect('/')

    # Si el usuario tiene un negocio asociado, ir a su mini-página admin
    if hasattr(request.user, 'negocio'):
        return redirect(f'/{request.user.negocio.slug}/admin/')

    # Si no tiene negocio ni es superadmin, ir al home
    return redirect('/')
