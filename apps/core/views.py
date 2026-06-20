"""
Vistas generales del sistema
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.views.generic import TemplateView
from apps.authentication.models import Usuario
from apps.negocios.models import Negocio
from .forms import RegistroNegocioForm
from .permissions import asignar_permisos_admin_negocio


def landing_page(request):
    """
    Landing page principal - Página de presentación del servicio
    """
    # Si ya está autenticado Y NO es superadmin, redirigir a su mini-página
    if request.user.is_authenticated and not request.user.is_superuser:
        if hasattr(request.user, 'negocio'):
            return redirect(f'/{request.user.negocio.slug}/admin/')

    # Para superadmin o usuarios no autenticados, mostrar landing
    context = {
        'title': 'FacilAdmin - Sistema de Gestión para Spas y Peluquerías',
        'total_negocios': Negocio.objects.filter(esta_activo=True).count(),
        'negocios': Negocio.objects.filter(esta_activo=True).order_by('-fecha_creacion') if request.user.is_superuser else None,
    }
    return render(request, 'landing/index.html', context)


def registro_negocio(request):
    """
    Formulario de registro para nuevos negocios
    """
    if request.method == 'POST':
        form = RegistroNegocioForm(request.POST)
        if form.is_valid():
            try:
                # Crear usuario administrador con permisos de staff
                usuario = Usuario.objects.create_user(
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password'],
                    nombre=form.cleaned_data['nombre_admin'],
                    telefono=form.cleaned_data['telefono_admin'],
                )
                # Dar permisos de staff para acceder al admin
                usuario.is_staff = True
                usuario.is_active = True
                usuario.save()

                # Crear negocio
                negocio = Negocio.objects.create(
                    administrador=usuario,
                    nombre=form.cleaned_data['nombre_negocio'],
                    tipo=form.cleaned_data['tipo_negocio'],
                    telefono=form.cleaned_data['telefono_negocio'],
                    ciudad=form.cleaned_data['ciudad'],
                    esta_activo=True,
                    acepta_reservas_online=True,
                )

                # Asignar permisos específicos para gestionar su negocio
                # Los filtros en los ModelAdmin aseguran que solo vea sus propios datos
                asignar_permisos_admin_negocio(usuario)

                # Login automático
                login(request, usuario)

                messages.success(
                    request,
                    f'¡Bienvenido a FacilAdmin! Tu negocio "{negocio.nombre}" ha sido creado exitosamente.'
                )

                # Redirigir a su panel de administración personalizado
                return redirect(f'/{negocio.slug}/admin/')

            except Exception as e:
                messages.error(request, f'Error al crear el negocio: {str(e)}')
    else:
        form = RegistroNegocioForm()

    context = {
        'title': 'Registra tu Negocio - FacilAdmin',
        'form': form,
    }
    return render(request, 'landing/registro.html', context)


def precios(request):
    """
    Página de planes y precios
    """
    context = {
        'title': 'Planes y Precios - FacilAdmin',
    }
    return render(request, 'landing/precios.html', context)


def como_funciona(request):
    """
    Página explicativa de cómo funciona el sistema
    """
    context = {
        'title': 'Cómo Funciona - FacilAdmin',
    }
    return render(request, 'landing/como_funciona.html', context)


def contacto(request):
    """
    Página de contacto
    """
    context = {
        'title': 'Contacto - FacilAdmin',
    }
    return render(request, 'landing/contacto.html', context)


def service_worker(request):
    """
    Sirve el Service Worker desde la raíz para que pueda controlar todo el sitio
    """
    from django.http import HttpResponse
    from django.conf import settings
    import os

    # Leer el archivo sw.js desde static
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'js', 'sw.js')

    try:
        with open(sw_path, 'r', encoding='utf-8') as f:
            sw_content = f.read()

        response = HttpResponse(sw_content, content_type='application/javascript')
        # Agregar header para permitir scope en toda la aplicación
        response['Service-Worker-Allowed'] = '/'
        return response
    except FileNotFoundError:
        return HttpResponse('Service Worker not found', status=404)
