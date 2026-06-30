# Guía: Sistema de Recuperación de Contraseña

## Resumen de Implementación

Se ha implementado un **sistema completo de recuperación de contraseña** con las siguientes características de seguridad:

### Características Principales

✅ **Protección contra ataques de fuerza bruta**
- Rate limiting en login: 10 intentos cada 5 minutos (más permisivo que antes)
- Rate limiting en recuperación: 3 solicitudes por hora (previene spam de emails)

✅ **Tokens seguros**
- UUID único por solicitud
- Expiración automática en 1 hora
- Un solo uso por token
- Almacenamiento de IP de solicitud

✅ **Seguridad adicional**
- No revela si un email existe en el sistema (previene enumeración de usuarios)
- Invalidación automática de tokens anteriores al solicitar uno nuevo
- Validación de contraseña (mínimo 8 caracteres)
- Indicador visual de fortaleza de contraseña

✅ **Mejor experiencia de usuario**
- Flujo intuitivo: Login → ¿Olvidaste tu contraseña? → Email → Restablecer
- Templates modernos con diseño consistente
- Mensajes claros y útiles
- Feedback visual en tiempo real

---

## Estructura de Archivos Implementados

### 1. Modelo de Datos
- `apps/authentication/models.py` - Modelo `TokenRecuperacion`
  - UUID token único
  - Fecha de creación y expiración
  - Estado (usado/no usado)
  - IP de solicitud
  - Métodos: `es_valido()`, `marcar_como_usado()`

### 2. Vistas
- `apps/authentication/views.py`:
  - `RateLimitedLoginView` - Login con rate limiting mejorado
  - `SolicitarRecuperacionView` - Solicitud de recuperación
  - `RestablecerPasswordView` - Cambio de contraseña con token

### 3. URLs
- `config/urls.py`:
  - `/login/` - Inicio de sesión
  - `/recuperar-password/` - Solicitar recuperación
  - `/recuperar-password/<token>/` - Restablecer con token

### 4. Templates
- `templates/registration/login.html` - Con botón "¿Olvidaste tu contraseña?"
- `templates/registration/solicitar_recuperacion.html` - Formulario de solicitud
- `templates/registration/restablecer_password.html` - Formulario de nueva contraseña
- `templates/emails/recuperacion_password.html` - Email HTML profesional

### 5. Migraciones
- `apps/authentication/migrations/0002_tokenrecuperacion.py`

---

## Cómo Probar Localmente

### Paso 1: Servidor en Ejecución
El servidor ya está corriendo en: http://127.0.0.1:8000/

### Paso 2: Flujo de Prueba Completo

#### 2.1 Intentar login fallido
1. Ve a http://127.0.0.1:8000/login/
2. Intenta ingresar con credenciales incorrectas
3. Verás el mensaje: "Credenciales inválidas. ¿Olvidaste tu contraseña?"

#### 2.2 Solicitar recuperación
1. Haz clic en **"¿Olvidaste tu contraseña?"**
2. Serás redirigido a: http://127.0.0.1:8000/recuperar-password/
3. Ingresa un email registrado en el sistema
4. Haz clic en **"Enviar Enlace de Recuperación"**

#### 2.3 Verificar email en consola
**IMPORTANTE**: Como estamos en desarrollo local, el email **NO se envía** realmente, sino que se **imprime en la consola** del servidor.

1. Revisa la consola donde está corriendo el servidor
2. Verás un mensaje similar a:
```
Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Subject: =?utf-8?q?Recuperaci=C3=B3n_de_contrase=C3=B1a_-_FacilAdmin?=
From: noreply@faciladmin.local
To: usuario@ejemplo.com
Date: Mon, 29 Jun 2026 20:00:00 -0000
Message-ID: <...>

Hola Usuario Name,

Recibimos una solicitud para restablecer la contraseña de tu cuenta...

Haz clic en el botón de abajo para crear una nueva contraseña:
http://127.0.0.1:8000/recuperar-password/a1b2c3d4-5678-90ef-ghij-klmnopqrstuv/
```

3. **Copia la URL del token** (la que termina con el UUID)

#### 2.4 Restablecer contraseña
1. Pega la URL en tu navegador
2. Verás el formulario de **"Nueva Contraseña"**
3. Ingresa una nueva contraseña (mínimo 8 caracteres)
4. Verás el indicador de fortaleza cambiar de color
5. Confirma la contraseña
6. Haz clic en **"Restablecer Contraseña"**
7. Serás redirigido al login con mensaje de éxito

#### 2.5 Verificar que funciona
1. Inicia sesión con la **nueva contraseña**
2. Debería funcionar correctamente

---

## Protecciones de Seguridad Implementadas

### 1. Rate Limiting
```python
# Login: 10 intentos / 5 minutos
@ratelimit(key='ip', rate='10/5m', method='POST', block=True)

# Solicitud de recuperación: 3 intentos / hora
@ratelimit(key='ip', rate='3/h', method='POST', block=True)
```

### 2. No Enumeración de Usuarios
```python
# Siempre muestra el mismo mensaje, exista o no el email
mensaje = "Si el correo está registrado, recibirás un enlace..."
```

### 3. Tokens de Un Solo Uso
```python
# Al usarse, el token se marca como usado
token_obj.marcar_como_usado()

# Validación estricta
def es_valido(self):
    return not self.usado and timezone.now() < self.fecha_expiracion
```

### 4. Expiración Automática
```python
# Los tokens expiran en 1 hora
self.fecha_expiracion = timezone.now() + timedelta(hours=1)
```

---

## Configuración de Email

### Desarrollo Local (actual)
```python
# config/settings/local.py
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@faciladmin.local'
```
Los emails se imprimen en la consola del servidor.

### Producción
Para producción, configura en `.env`:
```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password
```

**Nota**: Para Gmail, debes usar una "App Password", no tu contraseña normal.

---

## Base de Datos

Se creó una nueva tabla `authentication_tokenrecuperacion`:

```sql
CREATE TABLE authentication_tokenrecuperacion (
    id INTEGER PRIMARY KEY,
    token UUID UNIQUE,
    usuario_id INTEGER FOREIGN KEY,
    fecha_creacion DATETIME,
    fecha_expiracion DATETIME,
    usado BOOLEAN DEFAULT 0,
    ip_solicitud VARCHAR(45)
);

-- Índices para rendimiento
CREATE INDEX idx_token_usado ON authentication_tokenrecuperacion(token, usado);
CREATE INDEX idx_usuario_fecha ON authentication_tokenrecuperacion(usuario_id, fecha_creacion DESC);
```

---

## Archivos Modificados

1. ✅ `apps/authentication/models.py` - Nuevo modelo TokenRecuperacion
2. ✅ `apps/authentication/views.py` - Nuevas vistas de recuperación
3. ✅ `config/urls.py` - Nuevas rutas
4. ✅ `config/settings/local.py` - Configuración de email
5. ✅ `templates/registration/login.html` - Botón "¿Olvidaste tu contraseña?"
6. ✅ `templates/registration/solicitar_recuperacion.html` - Nuevo template
7. ✅ `templates/registration/restablecer_password.html` - Nuevo template
8. ✅ `templates/emails/recuperacion_password.html` - Nuevo template
9. ✅ `apps/authentication/migrations/0002_tokenrecuperacion.py` - Nueva migración

---

## Próximos Pasos Recomendados

### Para Producción:
1. ✅ Configurar servicio de email real (Gmail, SendGrid, AWS SES, etc.)
2. ⚠️  Considerar agregar CAPTCHA si hay muchos intentos de spam
3. ⚠️  Monitorear logs de intentos de recuperación sospechosos
4. ⚠️  Implementar notificación al usuario cuando se cambia su contraseña
5. ⚠️  Agregar límite de tokens activos por usuario (ej: máximo 3)

### Mejoras Opcionales:
- [ ] Agregar verificación de 2 factores (2FA)
- [ ] Historial de cambios de contraseña
- [ ] Notificación por SMS además de email
- [ ] Preguntas de seguridad como alternativa

---

## Ventajas vs Espera de 5 Minutos

| Aspecto | Sistema Anterior | Sistema Actual |
|---------|------------------|----------------|
| **UX del cliente** | ❌ Frustrante (esperar 5 min) | ✅ Fluido (recuperación inmediata) |
| **Seguridad** | ⚠️  Limitada (solo rate limiting) | ✅ Multicapa (rate limit + tokens + email) |
| **Conversión** | ❌ Pérdida de clientes | ✅ Alta retención |
| **Validación identidad** | ❌ Solo IP | ✅ Email + token único |
| **Escalabilidad** | ✅ Simple | ✅ Profesional |

---

## Soporte

Si encuentras algún problema durante las pruebas:
1. Revisa la consola del servidor para ver los emails
2. Verifica que las migraciones estén aplicadas: `python manage.py migrate`
3. Verifica que django-ratelimit esté instalado: `pip list | grep ratelimit`

**¡El sistema está listo para probar!** 🚀
