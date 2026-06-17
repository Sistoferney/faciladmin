"""
Signals para eliminar imágenes antiguas de Cloudinary
cuando se actualiza o elimina una Promoción
"""
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from .models import Promocion
import cloudinary.uploader


@receiver(pre_save, sender=Promocion)
def eliminar_imagen_anterior(sender, instance, **kwargs):
    """
    Elimina la imagen anterior de Cloudinary antes de guardar una nueva
    Evita duplicación de imágenes en Cloudinary
    """
    if not instance.pk:
        return  # Es un objeto nuevo, no hay imagen anterior

    try:
        # Obtener el objeto actual de la base de datos
        promocion_anterior = Promocion.objects.get(pk=instance.pk)

        # Verificar si la imagen cambió
        if promocion_anterior.imagen and promocion_anterior.imagen != instance.imagen:
            # Extraer el public_id de la URL de Cloudinary
            imagen_url = str(promocion_anterior.imagen)

            # El public_id está en la URL después de /upload/ y antes de la extensión
            if 'cloudinary' in imagen_url:
                try:
                    # Extraer public_id de la URL
                    parts = imagen_url.split('/')
                    # Buscar la parte después de 'upload'
                    upload_index = parts.index('upload')
                    # El public_id incluye la carpeta y el nombre del archivo sin extensión
                    public_id_parts = parts[upload_index + 2:]  # Salta version si existe
                    public_id = '/'.join(public_id_parts).rsplit('.', 1)[0]

                    # Eliminar de Cloudinary
                    cloudinary.uploader.destroy(public_id, invalidate=True)
                    print(f"✓ Imagen anterior eliminada de Cloudinary: {public_id}")
                except Exception as e:
                    print(f"Error al eliminar imagen de Cloudinary: {e}")

    except Promocion.DoesNotExist:
        pass


@receiver(post_delete, sender=Promocion)
def eliminar_imagen_al_borrar_promocion(sender, instance, **kwargs):
    """
    Elimina la imagen de Cloudinary cuando se elimina la promoción
    """
    if instance.imagen:
        try:
            imagen_url = str(instance.imagen)

            if 'cloudinary' in imagen_url:
                try:
                    parts = imagen_url.split('/')
                    upload_index = parts.index('upload')
                    public_id_parts = parts[upload_index + 2:]
                    public_id = '/'.join(public_id_parts).rsplit('.', 1)[0]

                    cloudinary.uploader.destroy(public_id, invalidate=True)
                    print(f"✓ Imagen eliminada de Cloudinary al borrar promoción: {public_id}")
                except Exception as e:
                    print(f"Error al eliminar imagen de Cloudinary: {e}")
        except Exception as e:
            print(f"Error al procesar eliminación de imagen: {e}")
