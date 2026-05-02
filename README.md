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
- **Base de Datos**: PostgreSQL
- **Tareas Asíncronas**: Celery + Redis
- **Notificaciones**: Twilio (WhatsApp/SMS)
- **Frontend**: HTML5, CSS3, Bootstrap/Tailwind

## Instalación

### 1. Clonar el repositorio

```bash
git clone <repository-url>
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
# Editar .env con tus configuraciones
```

### 5. Configurar PostgreSQL

Crear la base de datos:

```sql
CREATE DATABASE faciladmin_db;
CREATE USER faciladmin_user WITH PASSWORD 'tu_password';
GRANT ALL PRIVILEGES ON DATABASE faciladmin_db TO faciladmin_user;
```

### 6. Ejecutar migraciones

```bash
python manage.py migrate
```

### 7. Crear superusuario

```bash
python manage.py createsuperuser
```

### 8. Ejecutar servidor de desarrollo

```bash
python manage.py runserver
```

## Estructura del Proyecto

```
faciladmin/
├── config/              # Configuración principal del proyecto
├── apps/
│   ├── authentication/  # Autenticación de administradores
│   ├── negocios/        # Gestión de negocios y mini páginas
│   ├── servicios/       # Gestión de servicios
│   ├── clientes/        # CRM de clientes
│   ├── citas/           # Sistema de agenda y citas
│   ├── abonos/          # Sistema de abonos
│   ├── notificaciones/  # Envío de notificaciones
│   ├── fidelizacion/    # Sistema de fidelización
│   ├── promociones/     # Campañas y promociones
│   └── reportes/        # Dashboard y reportes
├── templates/           # Plantillas HTML
├── static/              # Archivos estáticos (CSS, JS, imágenes)
├── media/               # Archivos subidos por usuarios
└── requirements.txt
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
