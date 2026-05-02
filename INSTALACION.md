# Guía de Instalación - FacilAdmin

Esta guía te ayudará a configurar el proyecto en tu entorno local.

## Prerrequisitos

1. **Python 3.10+** instalado
2. **PostgreSQL 12+** instalado y corriendo
3. **Git** (opcional, para clonar el repositorio)

## Paso 1: Configurar PostgreSQL

Abre tu cliente de PostgreSQL (psql, pgAdmin, etc.) y ejecuta:

```sql
-- Crear la base de datos
CREATE DATABASE faciladmin_db;

-- Crear usuario (opcional, puedes usar tu usuario existente)
CREATE USER faciladmin_user WITH PASSWORD 'tu_password_seguro';

-- Otorgar privilegios
GRANT ALL PRIVILEGES ON DATABASE faciladmin_db TO faciladmin_user;

-- En PostgreSQL 15+, también necesitas:
\c faciladmin_db
GRANT ALL ON SCHEMA public TO faciladmin_user;
```

## Paso 2: Crear Entorno Virtual

```bash
# Navegar al directorio del proyecto
cd "e:\proyecto spa\faciladmin"

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate

# En Linux/Mac:
source venv/bin/activate
```

## Paso 3: Instalar Dependencias

```bash
pip install -r requirements.txt
```

Si encuentras errores con `psycopg2-binary`, intenta:
```bash
pip install psycopg2-binary --no-cache-dir
```

## Paso 4: Configurar Variables de Entorno

El archivo `.env` ya está creado. Edítalo con tus credenciales:

```bash
# Editar .env con tu editor favorito
notepad .env  # Windows
nano .env     # Linux/Mac
```

**Configuraciones importantes:**

```env
# Cambiar la contraseña de la base de datos
DB_PASSWORD=tu_password_de_postgres

# Si usaste un usuario diferente
DB_USER=tu_usuario

# Para producción, cambiar SECRET_KEY
SECRET_KEY=genera-una-clave-secreta-segura-aqui
```

## Paso 5: Ejecutar Migraciones

```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate
```

## Paso 6: Crear Superusuario

```bash
python manage.py createsuperuser
```

Ingresa:
- Email: tu_email@ejemplo.com
- Nombre: Tu Nombre
- Password: (tu contraseña segura)

## Paso 7: Crear Directorios de Media

```bash
# Windows PowerShell:
New-Item -ItemType Directory -Path "media", "staticfiles" -Force

# Linux/Mac o Git Bash:
mkdir -p media staticfiles
```

## Paso 8: Recolectar Archivos Estáticos

```bash
python manage.py collectstatic --noinput
```

## Paso 9: Ejecutar el Servidor

```bash
python manage.py runserver
```

Abre tu navegador en: http://localhost:8000

- **Panel Admin**: http://localhost:8000/admin
- **API**: http://localhost:8000/api/

## Paso 10: Configurar Celery (Opcional - Para Notificaciones)

### Instalar Redis

**Windows:**
1. Descargar desde: https://github.com/microsoftarchive/redis/releases
2. Ejecutar el instalador
3. Redis se ejecutará como servicio

**Linux:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

**Mac:**
```bash
brew install redis
brew services start redis
```

### Ejecutar Celery Worker

En una nueva terminal (con el entorno virtual activado):

```bash
# Worker
celery -A config worker -l info

# Beat (tareas programadas) - en otra terminal
celery -A config beat -l info
```

## Verificación de la Instalación

1. Accede al admin: http://localhost:8000/admin
2. Inicia sesión con tu superusuario
3. Verifica que puedas ver todas las aplicaciones instaladas

## Configuración Adicional

### Twilio (para WhatsApp y SMS)

1. Crear cuenta en https://www.twilio.com/
2. Obtener credenciales del Dashboard
3. Actualizar en `.env`:
   ```env
   TWILIO_ACCOUNT_SID=tu_account_sid
   TWILIO_AUTH_TOKEN=tu_auth_token
   TWILIO_PHONE_NUMBER=+1234567890
   TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567890
   ```

### Email

Para usar Gmail:

1. Habilitar "Aplicaciones menos seguras" o usar "Contraseñas de aplicación"
2. Actualizar en `.env`:
   ```env
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST_USER=tu_email@gmail.com
   EMAIL_HOST_PASSWORD=tu_password_de_aplicacion
   ```

## Solución de Problemas

### Error: "No module named 'decouple'"
```bash
pip install python-decouple
```

### Error de conexión a PostgreSQL
- Verificar que PostgreSQL esté corriendo
- Verificar credenciales en `.env`
- Verificar que el puerto 5432 esté disponible

### Error con migraciones
```bash
# Borrar migraciones y base de datos (¡cuidado en producción!)
python manage.py migrate --fake authentication zero
python manage.py migrate
```

## Siguiente Paso

Consulta [README.md](README.md) para información sobre el uso del sistema.

## Soporte

Para reportar problemas o hacer preguntas, crea un issue en el repositorio.
