# Configuración de Cloudinary para FacilAdmin

## 🎯 ¿Para qué sirve Cloudinary?

Cloudinary almacena las imágenes de forma **permanente** en la nube:
- Logos de negocios
- Imágenes de portada
- Fotos de servicios
- Cualquier imagen subida al sistema

**Sin Cloudinary:** Las imágenes se borran cada vez que Railway hace deploy.
**Con Cloudinary:** Las imágenes se guardan para siempre.

---

## 📋 Paso 1: Crear Cuenta Gratis en Cloudinary

1. **Ve a:** https://cloudinary.com/users/register_free

2. **Completa el registro:**
   - Nombre
   - Email
   - Contraseña

3. **Verifica tu email** (revisa bandeja de entrada)

4. **Inicia sesión:** https://cloudinary.com/users/login

---

## 🔑 Paso 2: Obtener Credenciales

Una vez dentro del Dashboard de Cloudinary:

1. **Ve a Dashboard** (página principal al iniciar sesión)

2. **Encontrarás esta información:**

```
Cloud name: xxxxxxxx
API Key: 123456789012345
API Secret: xxxxxxxxxxxxxxxxxxxxx
```

3. **Copia estos 3 valores** (los necesitarás en el siguiente paso)

---

## ⚙️ Paso 3: Configurar Variables en Railway

1. **Abre Railway Dashboard:** https://railway.app/

2. **Selecciona tu proyecto:** FacilAdmin

3. **Ve a la pestaña "Variables"**

4. **Agrega estas 3 variables:**

```
CLOUDINARY_CLOUD_NAME = tu_cloud_name_aqui
CLOUDINARY_API_KEY = tu_api_key_aqui
CLOUDINARY_API_SECRET = tu_api_secret_aqui
```

**Ejemplo:**
```
CLOUDINARY_CLOUD_NAME = faciladmin-spa
CLOUDINARY_API_KEY = 123456789012345
CLOUDINARY_API_SECRET = abcdefghijklmnopqrstuvwxyz
```

5. **Guarda los cambios**

6. **Railway hará redeploy automáticamente** (espera ~2 minutos)

---

## ✅ Paso 4: Verificar que Funciona

1. **Espera a que Railway termine el deploy**

2. **Ve a tu panel de Django Admin:**
   ```
   https://faciladmin-production.up.railway.app/admin/
   ```

3. **Ve a Negocios → Tu negocio**

4. **Sube una imagen** (logo o portada)

5. **Guarda**

6. **Abre la mini-página pública:**
   ```
   https://faciladmin-production.up.railway.app/{slug}/
   ```

7. **¿Se ve la imagen?** ✅ ¡Listo!

8. **Verifica en Cloudinary:**
   - Ve a https://cloudinary.com/console/media_library
   - Deberías ver tu imagen subida

---

## 🎨 Ventajas de Cloudinary

✅ **Permanente** - Nunca se borran las imágenes
✅ **Rápido** - CDN global (se cargan rápido desde cualquier parte del mundo)
✅ **Gratis** - 25 GB gratis para siempre
✅ **Automático** - Redimensiona y optimiza imágenes automáticamente
✅ **Respaldos** - Cloudinary hace backups automáticos

---

## 📊 Límites del Plan Gratuito

- **Almacenamiento:** 25 GB
- **Ancho de banda:** 25 GB/mes
- **Transformaciones:** 25,000/mes

Para un negocio de spas, esto alcanza para:
- ~50,000 imágenes (si cada una pesa 500KB)
- ~500 negocios con 100 imágenes cada uno

---

## 🔒 Seguridad

**Importante:** Nunca compartas tus credenciales de Cloudinary.

Las credenciales están en:
- ✅ Railway (Variables de entorno) - SEGURO
- ❌ NO las subas a GitHub
- ❌ NO las compartas por email/WhatsApp

---

## ❓ Troubleshooting

### **Problema: Las imágenes no se ven**

1. Verifica que las 3 variables estén en Railway
2. Verifica que no tengan espacios al inicio/final
3. Verifica que el deploy haya terminado
4. Revisa los logs de Railway por errores

### **Problema: Error al subir imágenes**

1. Verifica que las credenciales sean correctas
2. Verifica que la cuenta de Cloudinary esté activa
3. Revisa que no hayas excedido el límite gratuito

### **Problema: Imágenes viejas no se ven**

Las imágenes subidas ANTES de configurar Cloudinary se quedaron en Railway y se borraron.

**Solución:** Volver a subirlas desde el panel admin.

---

## 📞 Soporte

- **Cloudinary Docs:** https://cloudinary.com/documentation
- **Cloudinary Support:** support@cloudinary.com
- **Django Cloudinary Storage:** https://github.com/klis87/django-cloudinary-storage

---

## ✨ ¡Listo!

Ahora todas las imágenes se guardan permanentemente en Cloudinary y nunca se perderán con los deploys.

**Última actualización:** Junio 2026
