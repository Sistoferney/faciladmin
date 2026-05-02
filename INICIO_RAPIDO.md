# 🚀 Inicio Rápido - FacilAdmin (Versión SQLite)

Esta guía te permite empezar **SIN necesidad de instalar PostgreSQL**.

## ✅ Pasos Rápidos

### 1. Instalar dependencias (versión lite)

```bash
# Asegúrate de estar en el directorio del proyecto
cd "e:\proyecto spa\faciladmin"

# Activar entorno virtual (si no está activado)
venv\Scripts\activate

# Actualizar pip
python -m pip install --upgrade pip

# Instalar dependencias lite (sin PostgreSQL)
pip install -r requirements-lite.txt
```

### 2. Verificar configuración

El archivo `.env` ya está configurado para usar SQLite:
```
DB_ENGINE=sqlite
```

✅ No necesitas cambiar nada.

### 3. Crear la base de datos

```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate
```

### 4. Crear superusuario

```bash
python manage.py createsuperuser
```

Te pedirá:
- **Email**: tu_email@ejemplo.com
- **Nombre**: Tu Nombre Completo
- **Password**: (tu contraseña)

### 5. Ejecutar el servidor

```bash
python manage.py runserver
```

### 6. Acceder al sistema

Abre tu navegador en:
- **Panel Admin**: http://localhost:8000/admin

Inicia sesión con el email y contraseña que creaste.

## 🎯 Primeros pasos en el Admin

1. **Crear tu Negocio**:
   - Ve a "Negocios" → "Agregar negocio"
   - Llena los datos de tu spa/peluquería
   - Guarda

2. **Crear Servicios**:
   - Ve a "Servicios" → "Agregar servicio"
   - Define tus servicios (corte, spa, etc.)
   - Configura precio, duración y frecuencia

3. **Crear Clientes** (opcional):
   - Los clientes se crean automáticamente al agendar
   - O puedes crearlos manualmente en "Clientes"

4. **Crear Citas**:
   - Ve a "Citas" → "Agregar cita"
   - Selecciona cliente, servicio y fecha

## 📊 Características Disponibles

Con SQLite funcionan todas las características excepto:
- ✅ Gestión de negocios
- ✅ Servicios
- ✅ Clientes
- ✅ Citas
- ✅ Abonos
- ✅ Reportes
- ✅ Promociones
- ❌ Notificaciones automáticas (requiere Celery/Redis)

## 🔄 Migrar a PostgreSQL después (Opcional)

Cuando quieras usar PostgreSQL:

1. Instalar PostgreSQL
2. Instalar el driver:
   ```bash
   pip install psycopg2-binary
   ```
3. Crear la base de datos en PostgreSQL
4. Cambiar en `.env`:
   ```
   DB_ENGINE=postgresql
   DB_PASSWORD=tu_password
   ```
5. Ejecutar migraciones:
   ```bash
   python manage.py migrate
   ```

## ⚠️ Errores Comunes

### Error: "No module named 'decouple'"
```bash
pip install python-decouple
```

### Error al instalar Pillow
```bash
pip install Pillow --only-binary=:all:
```

### Error: "Table doesn't exist"
```bash
python manage.py migrate --run-syncdb
```

## 💡 Tips

- SQLite es perfecto para desarrollo y pruebas
- Todos los datos se guardan en `db.sqlite3`
- Puedes ver la base de datos con herramientas como DB Browser for SQLite
- Para producción, se recomienda PostgreSQL

## 🎉 ¡Listo!

Ya tienes el sistema funcionando. Explora el panel de administración y comienza a configurar tu negocio.

## ❓ ¿Necesitas Ayuda?

- Revisa [README.md](README.md) para más información
- Revisa [INSTALACION.md](INSTALACION.md) para instalación completa con PostgreSQL
