"""
Señales para gestión automática del onboarding
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Negocio
from .onboarding import OnboardingProgress, OnboardingManager


@receiver(post_save, sender=Negocio)
def actualizar_progreso_onboarding(sender, instance, created, **kwargs):
    """
    Actualiza el progreso del onboarding cuando se modifica un negocio
    """
    # Obtener o crear OnboardingProgress
    try:
        progress = instance.onboarding_progress
    except OnboardingProgress.DoesNotExist:
        progress = OnboardingProgress.objects.create(negocio=instance)

    # Recalcular progreso
    manager = OnboardingManager(instance)

    # Verificar y marcar pasos completados
    for paso_key in manager.PASOS.keys():
        if manager._paso_completado(paso_key):
            campo_completado = f"{paso_key}_completado"
            campo_fecha = f"{paso_key}_fecha"

            # Si no estaba marcado antes, marcarlo ahora
            if not getattr(progress, campo_completado, False):
                progress.marcar_paso_completado(paso_key)
        else:
            # Si ya no cumple el requisito, desmarcarlo
            campo_completado = f"{paso_key}_completado"
            if getattr(progress, campo_completado, False):
                setattr(progress, campo_completado, False)
                setattr(progress, f"{paso_key}_fecha", None)

    # Actualizar porcentaje
    progress.calcular_progreso()
    progress.save()
