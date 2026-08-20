"""
Vistas para el sistema de Onboarding Guiado
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from .models import Negocio
from .onboarding import OnboardingManager
from .forms import (
    DatosBasicosOnboardingForm,
    IdentidadVisualOnboardingForm,
    UbicacionContactoOnboardingForm,
    HorariosOnboardingForm
)


@login_required
def onboarding_dashboard(request):
    """
    Vista principal del onboarding que muestra el progreso general
    """
    # Verificar que el usuario tenga un negocio
    if not hasattr(request.user, 'negocio'):
        messages.error(request, 'Primero debes crear tu negocio.')
        return redirect('core:dashboard_redirect')

    negocio = request.user.negocio
    manager = OnboardingManager(negocio)

    # Obtener pasos con estado
    pasos = manager.obtener_pasos_con_estado()
    progreso = manager.progress.porcentaje_completado
    siguiente_paso = manager.siguiente_paso()

    context = {
        'negocio': negocio,
        'pasos': pasos,
        'progreso': progreso,
        'siguiente_paso': siguiente_paso,
        'onboarding_finalizado': manager.progress.onboarding_finalizado,
    }

    return render(request, 'negocios/onboarding/dashboard.html', context)


@login_required
def onboarding_paso_datos_basicos(request):
    """
    Paso 1: Configuración de datos básicos del negocio
    """
    negocio = get_object_or_404(Negocio, administrador=request.user)
    manager = OnboardingManager(negocio)

    if request.method == 'POST':
        form = DatosBasicosOnboardingForm(request.POST, instance=negocio)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Datos básicos guardados correctamente!')

            # Redirigir al siguiente paso o al dashboard
            siguiente_paso = manager.siguiente_paso()
            if siguiente_paso:
                return redirect(reverse(f'negocios:onboarding_paso_{siguiente_paso}'))
            return redirect('negocios:onboarding_dashboard')
    else:
        form = DatosBasicosOnboardingForm(instance=negocio)

    context = {
        'form': form,
        'paso_actual': 'datos_basicos',
        'paso_numero': 1,
        'total_pasos': len(manager.PASOS),
        'progreso': manager.progress.porcentaje_completado,
        'negocio': negocio,
    }

    return render(request, 'negocios/onboarding/paso_datos_basicos.html', context)


@login_required
def onboarding_paso_identidad_visual(request):
    """
    Paso 2: Configuración de identidad visual (logo, portada, colores)
    """
    negocio = get_object_or_404(Negocio, administrador=request.user)
    manager = OnboardingManager(negocio)

    if request.method == 'POST':
        form = IdentidadVisualOnboardingForm(request.POST, request.FILES, instance=negocio)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Identidad visual configurada!')

            siguiente_paso = manager.siguiente_paso()
            if siguiente_paso:
                return redirect(reverse(f'negocios:onboarding_paso_{siguiente_paso}'))
            return redirect('negocios:onboarding_dashboard')
    else:
        form = IdentidadVisualOnboardingForm(instance=negocio)

    context = {
        'form': form,
        'paso_actual': 'identidad_visual',
        'paso_numero': 2,
        'total_pasos': len(manager.PASOS),
        'progreso': manager.progress.porcentaje_completado,
        'negocio': negocio,
    }

    return render(request, 'negocios/onboarding/paso_identidad_visual.html', context)


@login_required
def onboarding_paso_ubicacion_contacto(request):
    """
    Paso 3: Configuración de ubicación y datos de contacto
    """
    negocio = get_object_or_404(Negocio, administrador=request.user)
    manager = OnboardingManager(negocio)

    if request.method == 'POST':
        form = UbicacionContactoOnboardingForm(request.POST, instance=negocio)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Ubicación y contacto guardados!')

            siguiente_paso = manager.siguiente_paso()
            if siguiente_paso:
                return redirect(reverse(f'negocios:onboarding_paso_{siguiente_paso}'))
            return redirect('negocios:onboarding_dashboard')
    else:
        form = UbicacionContactoOnboardingForm(instance=negocio)

    context = {
        'form': form,
        'paso_actual': 'ubicacion_contacto',
        'paso_numero': 3,
        'total_pasos': len(manager.PASOS),
        'progreso': manager.progress.porcentaje_completado,
        'negocio': negocio,
    }

    return render(request, 'negocios/onboarding/paso_ubicacion_contacto.html', context)


@login_required
def onboarding_paso_horarios(request):
    """
    Paso 4: Configuración de horarios de atención
    """
    negocio = get_object_or_404(Negocio, administrador=request.user)
    manager = OnboardingManager(negocio)

    if request.method == 'POST':
        form = HorariosOnboardingForm(request.POST, instance=negocio)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Horarios configurados!')

            siguiente_paso = manager.siguiente_paso()
            if siguiente_paso:
                return redirect(reverse(f'negocios:onboarding_paso_{siguiente_paso}'))
            return redirect('negocios:onboarding_dashboard')
    else:
        form = HorariosOnboardingForm(instance=negocio)

    context = {
        'form': form,
        'paso_actual': 'horarios',
        'paso_numero': 4,
        'total_pasos': len(manager.PASOS),
        'progreso': manager.progress.porcentaje_completado,
        'negocio': negocio,
    }

    return render(request, 'negocios/onboarding/paso_horarios.html', context)


@login_required
def onboarding_paso_servicios(request):
    """
    Paso 5: Agregar servicios (mínimo 3)
    """
    negocio = get_object_or_404(Negocio, administrador=request.user)
    manager = OnboardingManager(negocio)
    servicios = negocio.servicios.all()
    servicios_count = servicios.count()
    servicios_requeridos = 3

    servicios_faltantes = max(0, servicios_requeridos - servicios_count)

    context = {
        'paso_actual': 'servicios',
        'paso_numero': 5,
        'total_pasos': len(manager.PASOS),
        'progreso': manager.progress.porcentaje_completado,
        'negocio': negocio,
        'servicios': servicios,
        'servicios_count': servicios_count,
        'servicios_requeridos': servicios_requeridos,
        'servicios_faltantes': servicios_faltantes,
        'completado': servicios_count >= servicios_requeridos,
    }

    return render(request, 'negocios/onboarding/paso_servicios.html', context)


@login_required
def onboarding_saltar(request):
    """
    Permite al usuario saltar el onboarding
    """
    if hasattr(request.user, 'negocio'):
        manager = OnboardingManager(request.user.negocio)
        manager.saltar_onboarding()
        messages.info(request, 'Puedes completar tu perfil desde la configuración cuando quieras.')

    return redirect('core:dashboard_redirect')


@login_required
def onboarding_completar(request):
    """
    Marca el onboarding como completado manualmente
    Solo se permite si el progreso está al 100%
    """
    # Solo aceptar POST para seguridad
    if request.method != 'POST':
        return redirect('negocios:onboarding_dashboard')

    if not hasattr(request.user, 'negocio'):
        messages.error(request, 'No tienes un negocio registrado.')
        return redirect('core:dashboard_redirect')

    manager = OnboardingManager(request.user.negocio)

    # Validar que el progreso esté al 100%
    if manager.progress.porcentaje_completado < 100:
        messages.warning(request, f'Debes completar todos los pasos para finalizar. Progreso actual: {manager.progress.porcentaje_completado}%')
        return redirect('negocios:onboarding_dashboard')

    # Marcar como finalizado
    manager.progress.onboarding_finalizado = True
    manager.progress.save()
    messages.success(request, '¡Felicidades! Tu perfil está 100% configurado.')

    return redirect('core:dashboard_redirect')
