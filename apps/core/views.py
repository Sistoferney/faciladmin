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


def landing_page(request):
    """
    Landing page principal - Página de presentación del servicio
    """
    # Si ya está autenticado, redirigir al admin
    if request.user.is_authenticated:
        return redirect('/admin/')

    context = {
        'title': 'FacilAdmin - Sistema de Gestión para Spas y Peluquerías',
        'total_negocios': Negocio.objects.filter(esta_activo=True).count(),
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
                # Crear usuario administrador
                usuario = Usuario.objects.create_user(
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password'],
                    nombre=form.cleaned_data['nombre_admin'],
                    telefono=form.cleaned_data['telefono_admin'],
                )

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

                # Login automático
                login(request, usuario)

                messages.success(
                    request,
                    f'¡Bienvenido a FacilAdmin! Tu negocio "{negocio.nombre}" ha sido creado exitosamente.'
                )

                return redirect('/admin/')

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
