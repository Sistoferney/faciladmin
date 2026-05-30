# Guía de Despliegue en Railway

Esta guía te ayudará a desplegar FacilAdmin en Railway paso a paso.

## 📋 Requisitos Previos

- Cuenta en [Railway.app](https://railway.app/)
- Cuenta en GitHub con el código del proyecto
- Proyecto ya commiteado y pusheado a GitHub

## 🚀 Configuración de Ambientes

Este proyecto está configurado para manejar **dos ambientes**:

### 1. **Desarrollo Local** (config/settings/local.py)
- Base de datos: SQLite
- Debug: Activado
- Celery: Modo eager (sin Redis)
- Email: Console backend

### 2. **Producción** (config/settings/production.py)
- Base de datos: PostgreSQL (Railway)
- Debug: Desactivado
- Celery: Redis (opcional)
- Email: SMTP real
- Static files: WhiteNoise
- HTTPS: Forzado

El sistema detecta automáticamente el ambiente usando la variable `DJANGO_ENVIRONMENT`.

## 📦 Despliegue en Railway

### Paso 1: Crear Nuevo Proyecto

1. Inicia sesión en [Railway.app](https://railway.app/)
2. Click en **"New Project"**
3. Selecciona **"Deploy from GitHub repo"**
4. Autoriza Railway a acceder a tu GitHub
5. Selecciona el repositorio **faciladmin**

### Paso 2: Agregar PostgreSQL

1. En tu proyecto de Railway, click en **"+ New"**
2. Selecciona **"Database"** → **"Add PostgreSQL"**
3. Railway creará automáticamente la variable `DATABASE_URL`

### Paso 3: Configurar Variables de Entorno

En el dashboard de Railway, ve a tu servicio web → **Variables** y agrega:

#### ⚠️ Variables OBLIGATORIAS:

```bash
DJANGO_ENVIRONMENT=production
SECRET_KEY=tu-secret-key-super-segura-generala-nueva
ALLOWED_HOSTS=.railway.app,.up.railway.app
```

Para generar un SECRET_KEY seguro:
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

#### 📧 Variables Opcionales (Email):

```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_app_password_de_gmail
```

#### 📱 Variables Opcionales (Twilio - WhatsApp/SMS):

```bash
TWILIO_ACCOUNT_SID=tu_account_sid
TWILIO_AUTH_TOKEN=tu_auth_token
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567890
```

#### 🌐 Variables Opcionales (CORS):

```bash
CORS_ALLOWED_ORIGINS=https://tu-frontend.com,https://otro-dominio.com
```

### Paso 4: Agregar Redis (Opcional - Para Celery)

Si necesitas tareas asíncronas con Celery:

1. En tu proyecto, click en **"+ New"** → **"Database"** → **"Add Redis"**
2. Railway creará automáticamente la variable `REDIS_URL`
3. Agrega esta variable:
```bash
USE_CELERY_EAGER=False
```

Si NO usas Redis, Celery funcionará en modo "eager" (síncrono).

### Paso 5: Deploy

1. Railway detectará automáticamente:
   - `runtime.txt` → Versión de Python
   - `Procfile` → Comandos de inicio
   - `requirements.txt` → Dependencias

2. El deploy se ejecutará automáticamente y correrá:
   - `pip install -r requirements.txt`
   - `python manage.py migrate` (migraciones automáticas)
   - `gunicorn config.wsgi` (servidor de producción)

3. Espera a que el deploy termine (2-5 minutos)

### Paso 6: Crear Superusuario

Una vez desplegado:

1. Ve a tu proyecto en Railway
2. Click en tu servicio web → **Deployments** → **View Logs**
3. En la pestaña superior, busca **"Shell"** o **"SSH"**
4. Ejecuta:
```bash
python manage.py createsuperuser
```

### Paso 7: Recolectar Archivos Estáticos

Railway debería hacerlo automáticamente, pero si necesitas ejecutarlo manualmente:

```bash
python manage.py collectstatic --noinput
```

## 🌍 Acceder a tu Aplicación

Railway te proporcionará una URL automática:
```
https://faciladmin-production-XXXX.up.railway.app
```

Puedes encontrarla en: **Settings** → **Networking** → **Public Networking**

### Configurar Dominio Personalizado (Opcional)

1. Ve a **Settings** → **Networking**
2. Click en **"Custom Domain"**
3. Agrega tu dominio: `tudominio.com`
4. Configura el DNS según las instrucciones de Railway
5. Actualiza `ALLOWED_HOSTS` para incluir tu dominio:
```bash
ALLOWED_HOSTS=.railway.app,.up.railway.app,tudominio.com,www.tudominio.com
```

## 🔒 Seguridad en Producción

El archivo `config/settings/production.py` ya incluye:

- ✅ HTTPS forzado (`SECURE_SSL_REDIRECT=True`)
- ✅ Cookies seguras
- ✅ HSTS habilitado
- ✅ Protección XSS
- ✅ Protección contra clickjacking
- ✅ DEBUG=False

## 📊 Monitoreo

Railway proporciona:
- **Logs en tiempo real**: Ver errores y actividad
- **Métricas**: CPU, memoria, tráfico
- **Reinicio automático**: Si la app falla

Accede a los logs: **Deployments** → **View Logs**

## 🐛 Troubleshooting

### Error: "Application failed to respond"

1. Verifica logs en Railway
2. Asegúrate que `DATABASE_URL` existe
3. Verifica que `DJANGO_ENVIRONMENT=production`

### Error: "Static files not loading"

```bash
python manage.py collectstatic --noinput
```

### Error: "DisallowedHost"

Agrega el dominio a `ALLOWED_HOSTS`:
```bash
ALLOWED_HOSTS=.railway.app,.up.railway.app,tudominio.com
```

### Error: "Database connection failed"

1. Verifica que PostgreSQL esté agregado
2. Verifica que `DATABASE_URL` exista en variables

## 🔄 Actualizar la Aplicación

Railway hace deploy automático cuando haces push a GitHub:

```bash
git add .
git commit -m "Descripción de cambios"
git push origin main
```

Railway detectará el push y redesplegarán automáticamente.

## 💰 Costos

Railway incluye:
- ✅ **$5 USD gratis al mes** (créditos renovables)
- ✅ PostgreSQL incluido
- ✅ Redis opcional incluido
- ✅ ~500 horas de servicio/mes gratis

**Consumo aproximado:**
- Web service: ~$0.01/hora después del crédito
- PostgreSQL: Incluido en el plan
- Redis: Incluido en el plan

## 📚 Recursos Adicionales

- [Documentación de Railway](https://docs.railway.app/)
- [Railway Discord](https://discord.gg/railway)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/)

## 🔗 URLs Importantes

- **Panel Admin**: `https://tu-app.up.railway.app/admin/`
- **API Docs**: `https://tu-app.up.railway.app/api/`
- **Landing Page**: `https://tu-app.up.railway.app/`

---

¡Tu aplicación está lista en producción! 🎉
