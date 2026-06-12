"""
Signals para el modelo Negocio
Maneja la eliminación de imágenes antiguas en Cloudinary
"""
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from .models import Negocio
import cloudinary


@receiver(pre_save, sender=Negocio)
def eliminar_imagen_anterior(sender, instance, **kwargs):
    """
    Elimina la imagen anterior de Cloudinary cuando se sube una nueva
    Evita duplicación de imágenes
    """
    if not instance.pk:
        # Es un objeto nuevo, no hay imagen anterior que eliminar
        return

    try:
        # Obtener la instancia antigua de la base de datos
        old_instance = Negocio.objects.get(pk=instance.pk)

        # Verificar si el logo cambió
        if old_instance.logo and old_instance.logo != instance.logo:
            # Eliminar el logo antiguo de Cloudinary
            try:
                # Extraer el public_id de la URL
                public_id = old_instance.logo.name
                if public_id:
                    cloudinary.uploader.destroy(public_id)
                    print(f"✓ Logo anterior eliminado: {public_id}")
            except Exception as e:
                print(f"Error al eliminar logo anterior: {e}")

        # Verificar si la imagen de portada cambió
        if old_instance.imagen_portada and old_instance.imagen_portada != instance.imagen_portada:
            # Eliminar la imagen de portada antigua de Cloudinary
            try:
                public_id = old_instance.imagen_portada.name
                if public_id:
                    cloudinary.uploader.destroy(public_id)
                    print(f"✓ Imagen de portada anterior eliminada: {public_id}")
            except Exception as e:
                print(f"Error al eliminar imagen de portada anterior: {e}")

    except Negocio.DoesNotExist:
        # El objeto no existe aún en la BD
        pass


@receiver(post_delete, sender=Negocio)
def eliminar_imagenes_al_borrar_negocio(sender, instance, **kwargs):
    """
    Elimina todas las imágenes de Cloudinary cuando se elimina un negocio
    """
    # Eliminar logo
    if instance.logo:
        try:
            public_id = instance.logo.name
            if public_id:
                cloudinary.uploader.destroy(public_id)
                print(f"✓ Logo eliminado al borrar negocio: {public_id}")
        except Exception as e:
            print(f"Error al eliminar logo: {e}")

    # Eliminar imagen de portada
    if instance.imagen_portada:
        try:
            public_id = instance.imagen_portada.name
            if public_id:
                cloudinary.uploader.destroy(public_id)
                print(f"✓ Portada eliminada al borrar negocio: {public_id}")
        except Exception as e:
            print(f"Error al eliminar portada: {e}")
