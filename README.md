# FacilAdmin - Sistema de Gestión para Spas, Peluquerías y Barberías

Sistema integral de administración con mini página web responsiva para agendar citas y administrar clientes.

## Características Principales

- Mini página web personalizable para cada negocio
- Sistema de reservas de citas en tiempo real
- Gestión de clientes (CRM básico)
- Sistema de abonos con confirmación manual
- Notificaciones automáticas (WhatsApp, SMS, Email)
- Módulo de fidelización de clientes
- Promociones y campañas segmentadas
- Dashboard con reportes básicos
- 100% Responsive

## Tecnologías

- **Backend**: Django 5.0 + Django REST Framework
- **Base de Datos**: PostgreSQL / SQLite (desarrollo)
- **Tareas Asíncronas**: Celery + Redis (opcional)
- **Notificaciones**: Twilio (WhatsApp/SMS)
- **Frontend**: HTML5, CSS3, Bootstrap 5
- **Servidor Producción**: Gunicorn + WhiteNoise
- **Deploy**: Railway / Render (recomendado)

## 🚀 Inicio Rápido (Desarrollo Local)

### 1. Clonar el repositorio

```bash
git clone https://github.com/Sistoferney/faciladmin.git
cd faciladmin
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
# El proyecto usa SQLite por defecto en desarrollo, no necesitas configurar nada más
```

### 5. Ejecutar migraciones

```bash
python manage.py migrate
```

### 6. Crear superusuario

```bash
python manage.py createsuperuser
```

### 7. Ejecutar servidor de desarrollo

```bash
python manage.py runserver
```

### 8. Acceder a la aplicación

- **Landing Page**: http://localhost:8000/
- **Admin Panel**: http://localhost:8000/admin/
- **Registro de Negocio**: http://localhost:8000/registro/

---

## 📚 Guías de Configuración

### Desarrollo Local vs Producción

Este proyecto está configurado para funcionar en **dos ambientes**:

- **Local**: SQLite, Debug mode, sin Redis
- **Producción**: PostgreSQL, SSL, WhiteNoise, Gunicorn

📖 **Lee la guía completa**: [CONFIGURACION_AMBIENTES.md](CONFIGURACION_AMBIENTES.md)

### Despliegue en Railway

Para desplegar en producción (Railway):

📖 **Lee la guía paso a paso**: [DEPLOYMENT_RAILWAY.md](DEPLOYMENT_RAILWAY.md)

**Resumen rápido:**
1. Conecta tu repo de GitHub con Railway
2. Agrega PostgreSQL
3. Configura variables de entorno
4. Deploy automático ✅

---

## 🗂️ Configuración Opcional: PostgreSQL Local

Si prefieres usar PostgreSQL localmente (igual que producción):

### 1. Crear la base de datos

```sql
CREATE DATABASE faciladmin_db;
CREATE USER faciladmin_user WITH PASSWORD 'tu_password';
GRANT ALL PRIVILEGES ON DATABASE faciladmin_db TO faciladmin_user;
```

### 2. Actualizar .env

```env
DB_ENGINE=postgresql
DB_NAME=faciladmin_db
DB_USER=faciladmin_user
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432
```

### 3. Migrar

```bash
python manage.py migrate
```

## Estructura del Proyecto

```
faciladmin/
├── config/                     # Configuración principal
│   ├── settings/
│   │   ├── __init__.py        # Detección automática de ambiente
│   │   ├── base.py            # Configuración común
│   │   ├── local.py           # Desarrollo (SQLite)
│   │   └── production.py      # Producción (PostgreSQL)
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── authentication/        # Autenticación de administradores
│   ├── negocios/              # Gestión de negocios y mini páginas
│   ├── servicios/             # Gestión de servicios
│   ├── clientes/              # CRM de clientes
│   ├── citas/                 # Sistema de agenda y citas
│   ├── abonos/                # Sistema de abonos
│   ├── notificaciones/        # Envío de notificaciones
│   ├── fidelizacion/          # Sistema de fidelización
│   ├── promociones/           # Campañas y promociones
│   ├── reportes/              # Dashboard y reportes
│   └── core/                  # Vistas core (landing, registro)
├── templates/
│   ├── landing/               # Landing page
│   ├── registration/          # Login/registro
│   ├── minipagina/            # Mini-páginas públicas
│   └── admin_panel/           # Panel de administración
├── static/                    # Archivos estáticos
├── media/                     # Archivos subidos
├── .env.example               # Plantilla de variables de entorno
├── Procfile                   # Configuración Railway/Heroku
├── runtime.txt                # Versión de Python
├── requirements.txt           # Dependencias
├── DEPLOYMENT_RAILWAY.md      # Guía de despliegue
└── CONFIGURACION_AMBIENTES.md # Guía de configuración
```

## Módulos del Sistema

### 1. Autenticación
- Registro e inicio de sesión de administradores
- Recuperación de contraseña
- Modelo híbrido para clientes (sin registro formal)

### 2. Mini Página del Negocio
- URL única compartible
- Información del negocio
- Catálogo de servicios
- Sistema de reservas integrado
- Diseño responsive

### 3. Gestión de Servicios
- CRUD de servicios
- Configuración de duración, precio y frecuencia
- Activación/desactivación

### 4. Sistema de Citas
- Agenda diaria/semanal
- Disponibilidad en tiempo real
- Bloqueo de horarios
- Estados de citas (pendiente, confirmada, cancelada)

### 5. Gestión de Clientes
- Creación automática al agendar
- Identificación por número de teléfono
- Historial de citas
- Segmentación (nuevos, frecuentes, inactivos)

### 6. Sistema de Abonos
- Configuración de montos de abono
- Confirmación manual por administrador
- Estados y recordatorios de pago

### 7. Notificaciones
- WhatsApp (vía Twilio)
- SMS
- Email
- Confirmaciones, recordatorios y promociones

### 8. Fidelización
- Recordatorios automáticos
- Sugerencias de próximas citas
- Reactivación de clientes inactivos

### 9. Promociones
- Creación de campañas
- Segmentación de clientes
- Envío masivo

### 10. Reportes
- Número de citas
- Clientes recurrentes
- Ingresos estimados
- Horarios con baja ocupación

## Licencia

Proyecto privado - Todos los derechos reservados
