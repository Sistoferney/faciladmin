# Debug: Recuperación de Contraseña No Funciona

## 🔍 Pasos para Diagnosticar el Problema

### Paso 1: Verificar que el Servidor Esté Corriendo

1. Abre tu navegador
2. Ve a: http://127.0.0.1:8000/
3. ¿Ves la página de inicio de FacilAdmin?
   - ✅ SÍ → Continúa al Paso 2
   - ❌ NO → El servidor no está corriendo, inícialo

### Paso 2: Ir a Recuperación de Contraseña

1. Ve a: http://127.0.0.1:8000/recuperar-password/
2. ¿Ves el formulario de "Recuperar Contraseña"?
   - ✅ SÍ → Continúa al Paso 3
   - ❌ NO → Hay problema con las URLs

### Paso 3: Abrir Consola del Navegador

1. Presiona **F12** (Chrome/Edge) o **Ctrl+Shift+I** (Firefox)
2. Ve a la pestaña **"Console"**
3. Deja esta pestaña abierta

### Paso 4: Intentar Recuperación

1. En el formulario, ingresa un email que EXISTA en tu base de datos
   - Usuarios disponibles:
     - `sistofguarin@gmail.com`
     - `juan@gmail.com`
     - `sisto@gmail.com`
     - `sofiaguarinalvarez@gmail.com`
     - `patricia22@gmail.com`

2. Haz clic en **"Enviar Enlace de Recuperación"**

3. **Observa qué pasa**:

   **A) ¿Ves algún error ROJO en la consola (F12)?**
   - Ejemplo: "403 Forbidden", "500 Internal Server Error", etc.
   - Copia el error completo

   **B) ¿Qué pasa en la pantalla?**
   - [ ] Se queda en la misma página sin mensaje
   - [ ] Aparece mensaje de error
   - [ ] Te redirige a login
   - [ ] La página se recarga pero no pasa nada

   **C) ¿Ves algo en la consola del servidor?**
   - Revisa la terminal donde corre `python manage.py runserver`
   - ¿Hay algún error ahí?

### Paso 5: Revisar Logs del Servidor

En la terminal donde corre el servidor, deberías ver algo como:

**Si funciona**:
```
"POST /recuperar-password/ HTTP/1.1" 302 0
Content-Type: text/plain; charset="utf-8"
From: noreply@faciladmin.local
To: sistofguarin@gmail.com
Subject: Recuperación de contraseña - FacilAdmin
...
```

**Si hay error**:
```
ERROR: [detalles del error]
```

---

## 🛠️ Posibles Problemas y Soluciones

### Problema 1: Error 403 - CSRF Token

**Síntoma**: En consola del navegador ves "403 Forbidden"

**Causa**: Problema con CSRF token

**Solución**:
1. Limpia cookies del navegador (Ctrl+Shift+Del)
2. Recarga la página
3. Intenta de nuevo

### Problema 2: No Pasa Nada (Botón No Responde)

**Síntoma**: Haces clic y nada sucede

**Posibles causas**:
- JavaScript bloqueado
- Problema con el formulario

**Solución**:
1. Verifica en consola del navegador (F12) si hay errores JS
2. Intenta con otro navegador
3. Verifica que el botón sea de tipo `submit`

### Problema 3: Email No Existe en Base de Datos

**Síntoma**: Formulario se envía pero no ves email en consola

**Causa**: El email que ingresaste no existe en la DB

**Solución**:
Usa uno de estos emails que SÍ existen:
- `sistofguarin@gmail.com`
- `juan@gmail.com`
- `sisto@gmail.com`

### Problema 4: Error 500 - Server Error

**Síntoma**: Error 500 en consola o pantalla

**Causa**: Problema en el código del servidor

**Solución**:
1. Revisa los logs del servidor en la terminal
2. Copia el traceback completo del error
3. Compártelo para ayudarte a resolverlo

### Problema 5: Rate Limiting Bloqueado

**Síntoma**: Mensaje "Bloqueado por rate limiting"

**Causa**: Hiciste más de 3 intentos en la última hora

**Solución**:
1. Espera 1 hora
2. O reinicia el servidor (se limpian los contadores)
3. O usa otro navegador/modo incógnito

---

## 🧪 Prueba Manual Rápida

Ejecuta esto en la terminal para probar el sistema:

```bash
cd "e:\proyecto spa\faciladmin"
"venv/Scripts/python.exe" manage.py shell
```

Luego pega esto:

```python
from apps.authentication.models import Usuario, TokenRecuperacion
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

# Obtener un usuario
usuario = Usuario.objects.first()
print(f"Usuario: {usuario.email}")

# Crear token
token = TokenRecuperacion.objects.create(usuario=usuario, ip_solicitud='127.0.0.1')
print(f"Token creado: {token.token}")

# Crear URL
url = f"http://127.0.0.1:8000/recuperar-password/{token.token}/"
print(f"URL: {url}")

# Preparar email
contexto = {
    'usuario': usuario,
    'url_recuperacion': url,
    'expiracion_horas': 1,
}

html_message = render_to_string('emails/recuperacion_password.html', contexto)
plain_message = strip_tags(html_message)

# Enviar email (se imprimirá en consola)
try:
    send_mail(
        subject='Prueba - Recuperación de contraseña',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[usuario.email],
        html_message=html_message,
        fail_silently=False,
    )
    print("✅ Email enviado exitosamente!")
except Exception as e:
    print(f"❌ Error al enviar email: {e}")
```

**Si esto funciona**: El problema está en el formulario web o las URLs

**Si esto falla**: Hay un problema con la configuración de email o el modelo

---

## 📝 Información que Necesito

Para ayudarte mejor, dime:

1. **¿Qué paso exactamente está fallando?** (del 1 al 5)
2. **¿Qué ves en la consola del navegador?** (F12)
3. **¿Qué ves en la consola del servidor?** (terminal)
4. **¿Qué email intentaste usar?**
5. **Capturas de pantalla** (si es posible)

---

## ✅ Checklist de Verificación

- [ ] Servidor corriendo en http://127.0.0.1:8000/
- [ ] Puedo acceder a http://127.0.0.1:8000/recuperar-password/
- [ ] Veo el formulario completo
- [ ] Consola del navegador abierta (F12)
- [ ] Usé un email que SÍ existe en la DB
- [ ] Revisé los logs del servidor
- [ ] No hay errores en consola del navegador
- [ ] No hay errores en consola del servidor
