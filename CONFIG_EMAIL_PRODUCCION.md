# Configuración de Email en Producción - FacilAdmin

## 📧 Diferencias: Desarrollo vs Producción

### 🔧 Desarrollo Local (Actual)
```python
# config/settings/local.py
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@faciladmin.local'
```

**Comportamiento**:
- ❌ NO envía emails reales
- ✅ Imprime emails en la consola del servidor
- ✅ Útil para testing sin costos
- ✅ Ves contenido completo en terminal

**Ejemplo de Output**:
```
Content-Type: text/html; charset="utf-8"
From: noreply@faciladmin.local
To: sistoferney@gmail.com
Subject: Recuperación de contraseña - FacilAdmin

[Contenido HTML del email...]
http://127.0.0.1:8000/recuperar-password/token-uuid/
```

---

### 🚀 Producción (Railway)
```python
# config/settings/production.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# config/settings/base.py
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
```

**Comportamiento**:
- ✅ **Envía emails REALES** a la bandeja de entrada del usuario
- ✅ Usa servidor SMTP (Gmail, SendGrid, AWS SES, etc.)
- ✅ Emails llegan en segundos
- ✅ Branding profesional con HTML
- ⚠️ Requiere configuración de credenciales

---

## 🌐 Opciones de Servicio de Email

### Opción 1: Gmail (Recomendado para empezar) 📮

**Ventajas**:
- ✅ Gratis hasta 500 emails/día
- ✅ Fácil de configurar
- ✅ Confiable
- ✅ Familiar

**Límites**:
- ⚠️ 500 emails por día
- ⚠️ Requiere "App Password"

**Configuración**:

1. **Crear App Password en Google**:
   - Ve a: https://myaccount.google.com/apppasswords
   - Crea una contraseña de aplicación para "FacilAdmin"
   - Copia la contraseña generada (16 caracteres)

2. **Configurar en Railway**:
```bash
railway variables set EMAIL_HOST=smtp.gmail.com
railway variables set EMAIL_PORT=587
railway variables set EMAIL_USE_TLS=True
railway variables set EMAIL_HOST_USER=tu-email@gmail.com
railway variables set EMAIL_HOST_PASSWORD=abcd-efgh-ijkl-mnop
```

3. **Emails se enviarán desde**: `tu-email@gmail.com`

**Costo**: ✅ GRATIS (hasta 500/día)

---

### Opción 2: SendGrid (Recomendado para escala) 📨

**Ventajas**:
- ✅ 100 emails/día GRATIS
- ✅ 40,000/mes en plan gratuito (nuevo)
- ✅ Estadísticas detalladas
- ✅ API REST (opcional)
- ✅ Mejor deliverability

**Límites**:
- ⚠️ 100 emails/día en plan gratuito
- ✅ Planes pagos desde $19.95/mes (100k emails)

**Configuración**:

1. **Crear cuenta**: https://signup.sendgrid.com/
2. **Crear API Key** en SendGrid dashboard
3. **Verificar dominio** (opcional, recomendado)

**Configurar en Railway**:
```bash
railway variables set EMAIL_HOST=smtp.sendgrid.net
railway variables set EMAIL_PORT=587
railway variables set EMAIL_USE_TLS=True
railway variables set EMAIL_HOST_USER=apikey
railway variables set EMAIL_HOST_PASSWORD=tu-api-key-de-sendgrid
railway variables set DEFAULT_FROM_EMAIL=noreply@tudominio.com
```

**Costo**:
- ✅ GRATIS: 100/día
- 💰 Essentials: $19.95/mes (100k emails)

---

### Opción 3: AWS SES (Más económico a escala) 📬

**Ventajas**:
- ✅ $0.10 por cada 1,000 emails
- ✅ Extremadamente barato a escala
- ✅ 62,000 emails GRATIS en primer año
- ✅ Infraestructura de Amazon

**Desventajas**:
- ⚠️ Configuración más compleja
- ⚠️ Requiere verificar dominio
- ⚠️ "Sandbox mode" al inicio (límites)

**Configuración**:
```bash
railway variables set EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
railway variables set EMAIL_PORT=587
railway variables set EMAIL_USE_TLS=True
railway variables set EMAIL_HOST_USER=tu-aws-smtp-username
railway variables set EMAIL_HOST_PASSWORD=tu-aws-smtp-password
railway variables set DEFAULT_FROM_EMAIL=noreply@tudominio.com
```

**Costo**:
- ✅ GRATIS: 62,000/mes (primer año)
- 💰 Después: $0.10 / 1,000 emails

---

### Opción 4: Resend (Moderna y fácil) 💌

**Ventajas**:
- ✅ 3,000 emails/mes GRATIS
- ✅ Interfaz moderna
- ✅ Fácil configuración
- ✅ API REST excelente

**Configuración**:
1. Crear cuenta: https://resend.com/
2. Obtener API Key

```bash
railway variables set EMAIL_HOST=smtp.resend.com
railway variables set EMAIL_PORT=587
railway variables set EMAIL_USE_TLS=True
railway variables set EMAIL_HOST_USER=resend
railway variables set EMAIL_HOST_PASSWORD=tu-api-key
railway variables set DEFAULT_FROM_EMAIL=noreply@tudominio.com
```

**Costo**:
- ✅ GRATIS: 3,000/mes
- 💰 Pro: $20/mes (50k emails)

---

## 🚀 Configuración Paso a Paso para Railway

### Paso 1: Elegir Servicio de Email

**Recomendación inicial**: Gmail (más fácil para empezar)

### Paso 2: Obtener Credenciales

**Para Gmail**:
1. Ve a: https://myaccount.google.com/apppasswords
2. Crea contraseña de aplicación
3. Copia la contraseña de 16 caracteres

**Para SendGrid/Resend/AWS**:
- Crea cuenta en el servicio elegido
- Genera API Key
- Verifica dominio (opcional pero recomendado)

### Paso 3: Configurar Variables en Railway

**Opción A - Interfaz Web**:
1. Entra a tu proyecto en Railway
2. Ve a Variables
3. Agrega las variables:
   ```
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=tu-email@gmail.com
   EMAIL_HOST_PASSWORD=abcd-efgh-ijkl-mnop
   ```

**Opción B - CLI**:
```bash
# Instalar Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link proyecto
railway link

# Configurar variables
railway variables set EMAIL_HOST=smtp.gmail.com
railway variables set EMAIL_PORT=587
railway variables set EMAIL_USE_TLS=True
railway variables set EMAIL_HOST_USER=tu-email@gmail.com
railway variables set EMAIL_HOST_PASSWORD=tu-app-password
```

### Paso 4: Aplicar Migraciones (si no lo hiciste)

```bash
railway run python manage.py migrate
```

### Paso 5: Reiniciar la App

Railway reinicia automáticamente al cambiar variables.

---

## 🧪 Probar el Sistema en Producción

### Método 1: Desde la App

1. Ve a tu app en Railway: `https://tu-app.railway.app/login/`
2. Intenta login con credenciales incorrectas 3 veces
3. Haz clic en **"Recuperar Contraseña"**
4. Ingresa tu email
5. **Revisa tu bandeja de entrada** (y spam)
6. Verás el email profesional con el botón "Restablecer Mi Contraseña"
7. Haz clic y establece nueva contraseña

### Método 2: Shell de Django

```bash
railway run python manage.py shell
```

```python
from apps.authentication.models import Usuario, TokenRecuperacion
from django.core.mail import send_mail

# Obtener un usuario
usuario = Usuario.objects.first()

# Crear token
token = TokenRecuperacion.objects.create(usuario=usuario)

# Enviar email de prueba
from django.template.loader import render_to_string
from django.utils.html import strip_tags

url = f"https://tu-app.railway.app/recuperar-password/{token.token}/"
contexto = {
    'usuario': usuario,
    'url_recuperacion': url,
    'expiracion_horas': 1,
}

html = render_to_string('emails/recuperacion_password.html', contexto)
text = strip_tags(html)

send_mail(
    'Prueba de recuperación - FacilAdmin',
    text,
    'noreply@faciladmin.com',
    [usuario.email],
    html_message=html
)
```

---

## 📊 Comportamiento Esperado en Producción

### Flujo Completo

```
Usuario olvida contraseña
      ↓
Hace 3 intentos fallidos de login
      ↓
Ve botón naranja "Recuperar Contraseña"
      ↓
Ingresa su email: sistoferney@gmail.com
      ↓
Sistema crea token UUID único
      ↓
Envía email a través de SMTP (Gmail/SendGrid/etc)
      ↓
Email llega a bandeja en 5-30 segundos
      ↓
Usuario abre email en su correo
      ↓
Ve email profesional con branding de FacilAdmin
      ↓
Hace clic en "Restablecer Mi Contraseña"
      ↓
Es redirigido a: https://tu-app.railway.app/recuperar-password/uuid/
      ↓
Ingresa nueva contraseña (con validación)
      ↓
Token se marca como usado
      ↓
Redirigido a login con mensaje de éxito
      ↓
Inicia sesión con nueva contraseña ✅
```

### Tiempos de Entrega

| Servicio | Tiempo Promedio | Deliverability |
|----------|----------------|----------------|
| **Gmail** | 5-15 segundos | 95-98% |
| **SendGrid** | 2-10 segundos | 98-99% |
| **AWS SES** | 3-12 segundos | 97-99% |
| **Resend** | 2-8 segundos | 98-99% |

---

## ⚠️ Consideraciones de Seguridad

### 1. Protección de Credenciales

✅ **Nunca** subas credenciales a Git
```bash
# ❌ NUNCA hagas esto
EMAIL_HOST_PASSWORD=mi-password-real  # en código

# ✅ SIEMPRE usa variables de entorno
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
```

✅ Las variables en Railway están **encriptadas**
✅ Solo accesibles por tu aplicación

### 2. Rate Limiting (Ya implementado)

```python
# Ya configurado en el sistema
@ratelimit(key='ip', rate='3/h', method='POST', block=True)
def solicitar_recuperacion(request):
    # Solo 3 solicitudes por hora por IP
```

Esto previene:
- ❌ Spam de emails
- ❌ Abuso del sistema
- ❌ Costos innecesarios

### 3. Verificación de Dominio (Recomendado)

Para evitar que tus emails caigan en spam:

**Gmail**: No necesario si usas tu email personal
**SendGrid/AWS/Resend**:
- Verifica tu dominio (agrega registros DNS)
- Configura SPF, DKIM, DMARC
- Mejora deliverability de 70% a 99%

---

## 💰 Comparación de Costos

### Escenario 1: Negocio Pequeño (1,000 emails/mes)
| Servicio | Costo Mensual |
|----------|---------------|
| Gmail | ✅ GRATIS |
| SendGrid | ✅ GRATIS |
| AWS SES | ✅ GRATIS (primer año) |
| Resend | ✅ GRATIS |

### Escenario 2: Negocio Mediano (10,000 emails/mes)
| Servicio | Costo Mensual |
|----------|---------------|
| Gmail | ⚠️ Excede límite (necesitas Google Workspace) |
| SendGrid | ⚠️ $19.95/mes |
| AWS SES | ✅ $1.00/mes |
| Resend | ⚠️ $20/mes |

### Escenario 3: Negocio Grande (100,000 emails/mes)
| Servicio | Costo Mensual |
|----------|---------------|
| Gmail | ❌ No viable |
| SendGrid | 💰 $89.95/mes |
| AWS SES | ✅ $10/mes |
| Resend | 💰 $70/mes |

---

## 🔍 Monitoreo y Logs

### Ver emails enviados en Railway

```bash
# Ver logs en tiempo real
railway logs

# Buscar emails específicos
railway logs | grep "Recuperación de contraseña"
```

### Dashboard de SendGrid
- Emails enviados
- Emails abiertos (open rate)
- Clicks en enlaces
- Bounces (rebotes)
- Spam reports

### CloudWatch (AWS SES)
- Métricas de envío
- Bounces
- Complaints
- Deliverability

---

## 🛠️ Troubleshooting

### Problema 1: Emails no llegan

**Causas comunes**:
1. ❌ Credenciales incorrectas
2. ❌ Variables de entorno mal configuradas
3. ❌ Caen en spam
4. ❌ Email del destinatario inválido

**Solución**:
```bash
# Verificar variables
railway variables

# Ver logs de error
railway logs | grep ERROR

# Probar envío manual desde shell
railway run python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test', 'from@example.com', ['to@example.com'])
```

### Problema 2: Emails caen en spam

**Soluciones**:
1. ✅ Verificar dominio en el servicio de email
2. ✅ Configurar SPF, DKIM, DMARC
3. ✅ Usar dominio propio (no @gmail.com)
4. ✅ Pedir a usuarios agregar a contactos

### Problema 3: Error de autenticación

```
SMTPAuthenticationError: (535, b'5.7.8 Username and Password not accepted')
```

**Solución Gmail**:
- ✅ Usa App Password, NO tu contraseña de Gmail
- ✅ Habilita "Acceso de apps menos seguras" (si es necesario)

**Solución SendGrid/AWS**:
- ✅ Verifica que el API Key sea correcto
- ✅ Verifica que el API Key tenga permisos de envío

---

## ✅ Checklist de Configuración

Antes de ir a producción:

- [ ] Elegir servicio de email (Gmail, SendGrid, AWS, Resend)
- [ ] Crear cuenta en el servicio elegido
- [ ] Generar credenciales (App Password o API Key)
- [ ] Configurar variables de entorno en Railway
- [ ] Verificar dominio (opcional pero recomendado)
- [ ] Probar envío de email de prueba
- [ ] Verificar que emails no caen en spam
- [ ] Aplicar migraciones (`railway run python manage.py migrate`)
- [ ] Probar flujo completo de recuperación
- [ ] Monitorear logs los primeros días

---

## 📞 Soporte por Servicio

**Gmail**: https://support.google.com/mail
**SendGrid**: https://support.sendgrid.com
**AWS SES**: https://docs.aws.amazon.com/ses/
**Resend**: https://resend.com/docs

---

## 🎯 Recomendación Final

**Para empezar (0-1,000 usuarios)**:
- ✅ **Gmail** - Fácil, gratis, confiable

**Para crecer (1,000-10,000 usuarios)**:
- ✅ **SendGrid** - Balance entre facilidad y características

**Para escala (10,000+ usuarios)**:
- ✅ **AWS SES** - Más económico, mejor control

---

**¡Tu sistema de recuperación está listo para producción!** 🚀

Solo necesitas configurar las credenciales de email en Railway y funcionará automáticamente.
