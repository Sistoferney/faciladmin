# Configuración de Ambientes: Local vs Producción

FacilAdmin está configurado para funcionar en **dos ambientes separados**: desarrollo local y producción.

## 🏗️ Estructura de Settings

```
config/
├── settings/
│   ├── __init__.py       # Detecta automáticamente el ambiente
│   ├── base.py          # Configuración común
│   ├── local.py         # Configuración de desarrollo
│   └── production.py    # Configuración de producción
├── urls.py
└── wsgi.py
```

## 🔄 Detección Automática de Ambiente

El sistema detecta el ambiente usando la variable `DJANGO_ENVIRONMENT`:

| Variable | Ambiente | Settings Cargados |
|----------|----------|-------------------|
| `DJANGO_ENVIRONMENT=local` | Desarrollo | `config/settings/local.py` |
| `DJANGO_ENVIRONMENT=production` | Producción | `config/settings/production.py` |
| (sin definir) | Desarrollo (default) | `config/settings/local.py` |

## 🖥️ Ambiente LOCAL (Desarrollo)

### Características:

- ✅ **Base de datos**: SQLite (archivo local)
- ✅ **DEBUG**: Activado
- ✅ **Celery**: Modo eager (sin Redis necesario)
- ✅ **Email**: Console backend (imprime en terminal)
- ✅ **CORS**: Permisivo (permite todos los orígenes)
- ✅ **Static files**: Servidos por Django

### Configuración (.env):

```env
DJANGO_ENVIRONMENT=local
DEBUG=True
SECRET_KEY=django-insecure-development-key
ALLOWED_HOSTS=localhost,127.0.0.1
DB_ENGINE=sqlite
```

### Ejecutar en local:

```bash
# Activar entorno virtual
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Crear base de datos
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Ejecutar servidor
python manage.py runserver
```

### Opcional: PostgreSQL en local

Si prefieres usar PostgreSQL localmente (igual que producción):

1. Instala PostgreSQL
2. Crea la base de datos:
```sql
CREATE DATABASE faciladmin_db;
```
3. Actualiza tu `.env`:
```env
DB_ENGINE=postgresql
DB_NAME=faciladmin_db
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432
```

## ☁️ Ambiente PRODUCTION (Railway/Render)

### Características:

- ✅ **Base de datos**: PostgreSQL (Railway)
- ✅ **DEBUG**: Desactivado
- ✅ **Celery**: Redis (opcional)
- ✅ **Email**: SMTP real
- ✅ **CORS**: Restrictivo (solo dominios permitidos)
- ✅ **Static files**: WhiteNoise
- ✅ **HTTPS**: Forzado
- ✅ **Security**: Headers de seguridad activados

### Variables de entorno en Railway:

```env
DJANGO_ENVIRONMENT=production
SECRET_KEY=tu-secret-key-super-segura-NUNCA-la-misma-que-local
DEBUG=False
ALLOWED_HOSTS=.railway.app,.up.railway.app,tudominio.com

# Railway proporciona automáticamente:
DATABASE_URL=postgresql://...
REDIS_URL=redis://...  # Si agregas Redis
RAILWAY_STATIC_URL=https://...
```

### Deploy automático:

```bash
git add .
git commit -m "Cambios en producción"
git push origin main
```

Railway detecta el push y redespliega automáticamente.

## 🔀 Diferencias entre Ambientes

| Característica | Local | Producción |
|---------------|-------|------------|
| **Base de datos** | SQLite | PostgreSQL |
| **DEBUG** | True | False |
| **SECRET_KEY** | Insegura (hardcoded) | Segura (variable de entorno) |
| **Static files** | Django dev server | WhiteNoise |
| **HTTPS** | No forzado | Forzado (SSL redirect) |
| **CORS** | Permisivo | Restrictivo |
| **Email** | Console | SMTP real |
| **Celery** | Eager (sin Redis) | Redis (opcional) |
| **Logging** | INFO en consola | Verbose en consola |
| **Cookies** | No seguras | Seguras (HTTPS only) |

## 🧪 Testear Producción Localmente

Si quieres probar la configuración de producción en local:

```bash
# Configura variables de entorno
export DJANGO_ENVIRONMENT=production
export SECRET_KEY=test-secret-key
export DATABASE_URL=postgresql://user:pass@localhost/db
export ALLOWED_HOSTS=localhost,127.0.0.1
export DEBUG=False

# Recolectar static files
python manage.py collectstatic --noinput

# Ejecutar con gunicorn
gunicorn config.wsgi --bind 0.0.0.0:8000
```

## 🔒 Mejores Prácticas

### ❌ NUNCA hacer:

- ❌ Usar la misma `SECRET_KEY` en local y producción
- ❌ Hacer commit del archivo `.env`
- ❌ Activar `DEBUG=True` en producción
- ❌ Hardcodear contraseñas en el código
- ❌ Usar SQLite en producción

### ✅ SIEMPRE hacer:

- ✅ Usar `.env.example` como plantilla
- ✅ Generar `SECRET_KEY` única para producción
- ✅ Mantener `.env` en `.gitignore`
- ✅ Usar variables de entorno para secretos
- ✅ Probar en local antes de desplegar

## 📝 Archivo .env

### Local (.env):

```env
DJANGO_ENVIRONMENT=local
DEBUG=True
SECRET_KEY=django-insecure-local-key
ALLOWED_HOSTS=localhost,127.0.0.1
DB_ENGINE=sqlite
```

### Producción (Railway variables):

```env
DJANGO_ENVIRONMENT=production
SECRET_KEY=genera-una-key-super-segura-y-unica
DEBUG=False
ALLOWED_HOSTS=.railway.app,tudominio.com
# DATABASE_URL lo proporciona Railway automáticamente
```

## 🆘 Troubleshooting

### "ModuleNotFoundError: No module named 'config.settings.local'"

**Solución**: Verifica que existe `config/settings/local.py`

### "ALLOWED_HOSTS setting"

**Solución**: Agrega tu dominio a `ALLOWED_HOSTS`:
```env
ALLOWED_HOSTS=localhost,127.0.0.1,tudominio.com
```

### "No module named 'whitenoise'"

**Solución**: Instala las dependencias:
```bash
pip install -r requirements.txt
```

### Diferencias entre local y producción

Si algo funciona en local pero no en producción:

1. Verifica las variables de entorno en Railway
2. Revisa los logs: `railway logs`
3. Asegúrate que `DJANGO_ENVIRONMENT=production`
4. Verifica que `collectstatic` se ejecutó

## 🔄 Migrar de settings.py a settings/

Si tenías un solo archivo `config/settings.py` (configuración antigua):

1. **Haz backup** del archivo original
2. Los nuevos archivos ya están creados en `config/settings/`
3. Verifica que tu `.env` tenga `DJANGO_ENVIRONMENT=local`
4. Elimina o renombra `config/settings.py.old`

## 📚 Recursos

- [Django Settings Best Practices](https://docs.djangoproject.com/en/5.0/topics/settings/)
- [12 Factor App](https://12factor.net/)
- [Railway Docs](https://docs.railway.app/)

---

Con esta configuración puedes desarrollar localmente con SQLite y desplegar en Railway con PostgreSQL sin cambiar código.
