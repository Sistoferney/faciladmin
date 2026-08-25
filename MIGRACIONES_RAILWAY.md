# 🚀 Migraciones Automáticas en Railway

## ✅ Cómo Funciona

Railway ejecuta **automáticamente** las migraciones cada vez que se hace un deploy.

### Proceso Automático

Cuando hagas `git push origin main`, Railway:

1. **Detecta el push** → Inicia nuevo deployment
2. **Instala dependencias** → `pip install -r requirements.txt`
3. **Ejecuta Procfile** → Lee el archivo `Procfile`
4. **Corre migraciones** → `python manage.py migrate --noinput`
5. **Recolecta estáticos** → `python manage.py collectstatic --noinput`
6. **Inicia servidor** → `gunicorn config.wsgi`

### Archivo Procfile (Ya configurado)

```
web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn config.wsgi --log-file - --timeout 120 --workers 2 --bind 0.0.0.0:$PORT
```

**Explicación:**
- `python manage.py migrate --noinput` → Aplica todas las migraciones pendientes
- `&&` → Solo continúa si el comando anterior fue exitoso
- `--noinput` → No requiere confirmación manual

---

## 📦 Migraciones en Este Push

### Nueva migración que se aplicará:

```
apps/notificaciones/migrations/0003_clientepushsubscription.py
```

**Qué hace:**
- Crea tabla `notificaciones_clientepushsubscription`
- Campos: cliente, endpoint, auth, p256dh, user_agent, activa
- Índices para optimizar consultas por cliente
- Foreign key a la tabla de clientes

**Estado:**
- ✅ Probada localmente
- ✅ Aplicada en SQLite local sin errores
- ✅ Compatible con PostgreSQL (Railway usa PostgreSQL)

### Migraciones anteriores (ya aplicadas en Railway):

```
apps/notificaciones/migrations/0001_initial.py
apps/notificaciones/migrations/0002_alter_notificacion_canal.py
```

---

## 🔄 Flujo Completo del Deploy

### 1. Antes del Push (Local - YA HECHO)

```bash
✅ python manage.py makemigrations  # Crear migración
✅ python manage.py migrate          # Probar localmente
✅ git add ...                        # Agregar archivos
✅ git commit -m "..."                # Crear commit
```

### 2. Durante el Push

```bash
git push origin main
```

**Railway detecta automáticamente:**
- ✅ Nuevos commits en main
- ✅ Cambios en código Python
- ✅ Nueva migración en apps/notificaciones/migrations/

### 3. Durante el Deploy (Automático en Railway)

**Railway ejecuta:**

```bash
# 1. Clonar nuevo código
git clone ...

# 2. Instalar dependencias (incluyendo pywebpush nuevo)
pip install -r requirements.txt

# 3. Aplicar migraciones (AUTOMÁTICO)
python manage.py migrate --noinput

# Output esperado:
# Operations to perform:
#   Apply all migrations: notificaciones, clientes, negocios, ...
# Running migrations:
#   Applying notificaciones.0003_clientepushsubscription... OK

# 4. Recolectar estáticos
python manage.py collectstatic --noinput

# 5. Reiniciar servidor
gunicorn config.wsgi
```

### 4. Después del Deploy (Verificación)

**Cómo verificar que la migración se aplicó:**

1. **Ver logs de Railway:**
   - Railway Dashboard → Tu servicio → Deployments → View Logs
   - Buscar: `"Applying notificaciones.0003_clientepushsubscription... OK"`

2. **Verificar en Django Admin:**
   - Ir a: `https://tu-app.up.railway.app/admin/`
   - Verificar que aparezca "Suscripciones Push de Clientes" en el menú

3. **Verificar en Shell de Railway:**
   ```bash
   python manage.py showmigrations notificaciones

   # Output esperado:
   # notificaciones
   #  [X] 0001_initial
   #  [X] 0002_alter_notificacion_canal
   #  [X] 0003_clientepushsubscription  ← Debe tener [X]
   ```

---

## 🛡️ Seguridad y Rollback

### ¿Qué pasa si la migración falla?

Railway tiene protección automática:

1. **Si la migración falla:**
   - Railway NO inicia el nuevo servidor
   - Mantiene la versión anterior funcionando
   - Muestra error en los logs

2. **Para rollback manual:**
   ```bash
   # En Shell de Railway
   python manage.py migrate notificaciones 0002  # Volver a migración anterior
   ```

3. **Revertir el código:**
   ```bash
   # Local
   git revert HEAD
   git push origin main
   ```

### ¿Es segura esta migración?

✅ **SÍ, totalmente segura porque:**
- Solo **CREA** una nueva tabla (no modifica ni elimina datos)
- No afecta tablas existentes
- No requiere downtime
- Es reversible

---

## 📋 Checklist Pre-Push

Antes de hacer `git push origin main`, verifica:

- ✅ Migración creada: `0003_clientepushsubscription.py`
- ✅ Migración probada localmente (9/9 tests pasaron)
- ✅ Dependencia `pywebpush==1.14.0` agregada a requirements.txt
- ✅ Código committed (2 commits listos)
- ✅ Procfile configurado con `migrate --noinput`

**TODO LISTO PARA PUSH** ✅

---

## 🎯 Después del Push

### Acciones automáticas de Railway:

1. ⏱️ **Deploy tarda ~3-5 minutos**
2. 📦 Instala pywebpush y otras dependencias
3. 🗄️ Aplica migración 0003
4. 📁 Recolecta archivos estáticos
5. 🚀 Reinicia servidor con nuevo código
6. ✅ App funcionando con nueva funcionalidad

### Acciones manuales (opcionales):

1. **Verificar logs** → Ver que migración se aplicó correctamente
2. **Probar en admin** → Ver nuevo modelo en Django Admin
3. **Probar funcionalidad** → Agendar cita y recibir notificación push

---

## 🔍 Monitoreo del Deploy

### Dónde ver el progreso:

**Railway Dashboard:**
```
Tu Proyecto → faciladmin (servicio) → Deployments
```

**Logs en tiempo real:**
```
Deployments → Latest → View Logs
```

**Busca estas líneas:**
```
✓ Installing dependencies from requirements.txt
✓ pywebpush==1.14.0 successfully installed
✓ Applying notificaciones.0003_clientepushsubscription... OK
✓ Starting gunicorn
✓ Deployment successful
```

---

## ❓ FAQ

### ¿Tengo que correr las migraciones manualmente?
**No.** Railway las ejecuta automáticamente con el Procfile.

### ¿Qué pasa con los datos existentes?
**Nada.** Esta migración solo crea una tabla nueva, no toca datos existentes.

### ¿Puedo revertir la migración?
**Sí.** Desde el Shell de Railway o haciendo rollback del código.

### ¿Cuánto tarda el deploy?
**3-5 minutos** en promedio.

### ¿Habrá downtime?
**~10-30 segundos** durante el reinicio del servidor.

---

## ✅ Conclusión

**Las migraciones en Railway son 100% automáticas.**

Solo necesitas hacer:
```bash
git push origin main
```

Railway se encarga del resto. 🎉

---

**Última actualización:** 2026-08-24
**Migraciones pendientes:** 1 (0003_clientepushsubscription)
**Estado:** Listo para push ✅
