# Guía de Configuración: Redis + Celery en Railway

## 🎯 Objetivo

Configurar Redis y Celery (worker + beat) en Railway para habilitar:
- ✅ Recordatorios automáticos de citas 24h antes
- ✅ Notificaciones push asíncronas
- ✅ Verificación de abonos pendientes
- ✅ Detección de clientes inactivos
- ✅ Sugerencias de próxima cita

---

## 📋 Requisitos Previos

- ✅ Proyecto desplegado en Railway
- ✅ Código actualizado con los fixes recientes (Procfile con worker/beat)
- ✅ Acceso al dashboard de Railway

---

## 🚀 Paso 1: Agregar Redis

### 1.1 En el Dashboard de Railway

1. **Ir a tu proyecto:**
   ```
   https://railway.app/project/{tu-proyecto-id}
   ```

2. **Hacer clic en "+ New"** (esquina superior derecha)

3. **Seleccionar "Database"**

4. **Seleccionar "Add Redis"**

   Railway automáticamente:
   - Crea una instancia de Redis
   - Genera la variable `REDIS_URL`
   - La comparte con todos los servicios del proyecto

5. **Verificar que se creó:**
   - Deberías ver un nuevo servicio llamado "Redis"
   - Estado: "Active" (verde)

### 1.2 Verificar Variables de Entorno

1. **Ir a tu servicio principal (web)**

2. **Click en "Variables"**

3. **Verificar que existe `REDIS_URL`:**
   ```
   REDIS_URL=redis://default:xxxxxxxxx@...
   ```

   Si no aparece automáticamente:
   - Click en "Raw Editor"
   - Buscar `REDIS_URL` en la lista
   - Railway debería haberla agregado automáticamente

---

## 🔧 Paso 2: Crear Servicio Celery Worker

El **worker** procesa tareas asíncronas (envío de notificaciones, etc.)

### 2.1 Crear Nuevo Servicio

1. **Click en "+ New"** (esquina superior derecha)

2. **Seleccionar "GitHub Repo"**

3. **Seleccionar el MISMO repositorio** que tu app web

4. **Railway creará un nuevo servicio**

### 2.2 Configurar el Servicio Worker

1. **Click en el nuevo servicio**

2. **Click en "Settings"** (engranaje)

3. **En "Deploy":**
   - **Start Command:** Cambiar de `web` a `worker`
   - O escribir manualmente:
     ```
     celery -A config worker --loglevel=info --concurrency=2
     ```

4. **En "Service Name":**
   - Renombrar a: `celery-worker`

5. **Verificar Variables:**
   - Click en "Variables"
   - Asegurarse de que tenga acceso a:
     - `REDIS_URL` ✅
     - `DATABASE_URL` ✅
     - `DJANGO_SETTINGS_MODULE` ✅
     - Todas las demás variables del proyecto

6. **Click en "Deploy"** (si no despliega automáticamente)

### 2.3 Verificar que Funciona

1. **Click en "Deployments"**

2. **Click en el deployment activo**

3. **Click en "View Logs"**

4. **Deberías ver:**
   ```
   [2024-XX-XX XX:XX:XX] celery@xxxxxxxx ready.
   [2024-XX-XX XX:XX:XX] Connected to redis://...
   ```

   **Errores comunes:**
   - ❌ `Error: Redis connection refused` → Redis no está activo
   - ❌ `ModuleNotFoundError: celery` → Falta en requirements.txt
   - ❌ `App not configured` → Falta DJANGO_SETTINGS_MODULE

---

## ⏰ Paso 3: Crear Servicio Celery Beat

El **beat** programa tareas periódicas (recordatorios a las 10 AM, etc.)

### 3.1 Crear Nuevo Servicio

1. **Click en "+ New"**

2. **Seleccionar "GitHub Repo"**

3. **Seleccionar el MISMO repositorio**

### 3.2 Configurar el Servicio Beat

1. **Click en el nuevo servicio**

2. **Click en "Settings"**

3. **En "Deploy":**
   - **Start Command:** Cambiar a `beat`
   - O escribir manualmente:
     ```
     celery -A config beat --loglevel=info
     ```

4. **En "Service Name":**
   - Renombrar a: `celery-beat`

5. **⚠️ IMPORTANTE - Configurar Replicas:**
   - Click en "Settings" → "Scaling"
   - **Replicas: 1 (fijo)**
   - **NUNCA debe haber más de 1 instancia de beat**
   - Múltiples beats enviarían notificaciones duplicadas

6. **Verificar Variables:**
   - Igual que worker, debe tener acceso a todas las variables

7. **Click en "Deploy"**

### 3.3 Verificar que Funciona

1. **View Logs del servicio beat**

2. **Deberías ver:**
   ```
   [2024-XX-XX XX:XX:XX] celery beat v5.x.x is starting.
   [2024-XX-XX XX:XX:XX] Scheduler: DatabaseScheduler
   [2024-XX-XX XX:XX:XX] LocalTime -> 2024-XX-XX XX:XX:XX
   ```

   Y cada cierto tiempo:
   ```
   Scheduler: Sending due task enviar_recordatorios_citas
   Scheduler: Sending due task verificar_abonos_pendientes
   ```

---

## 🧪 Paso 4: Probar que Todo Funciona

### 4.1 Verificar Conexiones

**En el dashboard de Railway:**

1. **Deberías tener 4 servicios:**
   - 🟢 **faciladmin** (web)
   - 🟢 **Redis**
   - 🟢 **celery-worker**
   - 🟢 **celery-beat**

2. **Todos en estado "Active"**

### 4.2 Probar Tarea Asíncrona

**Opción 1: Desde Django Shell**

1. **En tu terminal local:**
   ```bash
   railway run python manage.py shell
   ```

2. **Ejecutar:**
   ```python
   from apps.notificaciones.tasks import enviar_confirmacion_cita

   # Enviar tarea de prueba (reemplazar con ID de cita real)
   result = enviar_confirmacion_cita.delay(1)

   print(f"Tarea enviada: {result.id}")
   ```

3. **Ver logs del worker:**
   - Railway Dashboard → celery-worker → View Logs
   - Deberías ver que procesa la tarea

**Opción 2: Crear una Cita**

1. **Agenda una cita desde la mini-página:**
   ```
   https://faciladmin.app/spa-ilusion/
   ```

2. **Verifica logs del worker:**
   - Debería mostrar que envía la notificación

3. **Verifica en admin de Django:**
   - `/admin/notificaciones/notificacion/`
   - Debería aparecer la notificación enviada

### 4.3 Verificar Tareas Programadas

**Desde Django Admin:**

1. **Ir a:**
   ```
   https://faciladmin.app/admin/django_celery_beat/
   ```

2. **Deberías ver las tareas programadas:**
   - `enviar_recordatorios_citas` - Diario 10:00 AM
   - `verificar_abonos_pendientes` - Diario 9:00 AM
   - `detectar_clientes_inactivos` - Semanal
   - `enviar_sugerencias_proxima_cita` - Semanal

**Ver logs de beat:**
- Railway Dashboard → celery-beat → View Logs
- Verifica que muestre "Scheduler: Sending due task..."

---

## 📊 Arquitectura Final

```
┌─────────────────────────────────────────────────────┐
│                   RAILWAY PROJECT                    │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐      ┌──────────────┐            │
│  │   faciladmin │◄─────┤    Redis     │            │
│  │     (web)    │      └──────────────┘            │
│  └──────────────┘              ▲                    │
│         │                      │                    │
│         │                      │                    │
│         ▼                      │                    │
│  ┌──────────────┐              │                    │
│  │   Postgres   │              │                    │
│  │  (Database)  │              │                    │
│  └──────────────┘              │                    │
│                                │                    │
│  ┌──────────────┐              │                    │
│  │celery-worker │──────────────┘                    │
│  │  (procesa    │                                   │
│  │   tareas)    │                                   │
│  └──────────────┘                                   │
│                                                      │
│  ┌──────────────┐                                   │
│  │ celery-beat  │──────────────┐                    │
│  │  (programa   │              │                    │
│  │   tareas)    │              ▼                    │
│  └──────────────┘       (10:00 AM) →                │
│                        enviar_recordatorios         │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## 🐛 Troubleshooting

### Worker no se conecta a Redis

**Síntoma:**
```
Error: Redis connection refused
```

**Solución:**
1. Verifica que Redis esté activo (verde)
2. Verifica que `REDIS_URL` exista en variables
3. Redeploy del worker

### Beat envía tareas duplicadas

**Síntoma:**
- Clientes reciben 2+ recordatorios

**Solución:**
1. Verifica que solo hay 1 instancia de beat
2. Settings → Scaling → Replicas: 1

### Tareas no se procesan

**Síntoma:**
- Las tareas se encolan pero nunca se ejecutan

**Solución:**
1. Verifica que worker esté activo
2. Ver logs del worker para errores
3. Verifica que worker tenga acceso a Database

### "No module named 'celery'"

**Síntoma:**
```
ModuleNotFoundError: No module named 'celery'
```

**Solución:**
1. Verifica que `celery>=5.3.0` esté en requirements.txt
2. Redeploy del servicio

### Beat no programa tareas

**Síntoma:**
- Logs de beat no muestran "Sending due task"

**Solución:**
1. Verifica config/celery.py
2. Verifica que beat tenga acceso a Database (usa DatabaseScheduler)
3. Redeploy de beat

---

## 💰 Costos en Railway

**Plan Hobby ($5/mes):**
- ✅ Incluye $5 de crédito mensual
- Cada servicio consume recursos:
  - **Web (faciladmin):** ~$3-4/mes
  - **Redis:** ~$1/mes
  - **Worker:** ~$0.50/mes
  - **Beat:** ~$0.25/mes

**Total estimado:** ~$4.75/mes (dentro del plan Hobby)

**Plan Pro ($20/mes):**
- Recursos ilimitados
- Mejor para producción

---

## ✅ Checklist Final

Antes de considerar que todo funciona:

- [ ] Redis activo y accesible
- [ ] Worker desplegado y en logs dice "ready"
- [ ] Beat desplegado y programa tareas
- [ ] Variables de entorno compartidas entre servicios
- [ ] Crear una cita de prueba → notificación se envía
- [ ] Verificar logs: web, worker, beat (sin errores)
- [ ] Verificar en admin: tareas programadas visibles
- [ ] Solo 1 instancia de beat corriendo

---

## 🎉 Resultado Final

**Antes:**
- ❌ Recordatorios nunca se enviaban
- ❌ Notificaciones bloqueaban requests HTTP
- ❌ Sin tareas programadas
- ❌ Abonos vencidos nunca se detectaban

**Después:**
- ✅ Recordatorios automáticos 10:00 AM
- ✅ Notificaciones asíncronas (instantáneas)
- ✅ Tareas programadas funcionando
- ✅ Abonos vencidos detectados diariamente
- ✅ Sistema escalable y robusto
- ✅ **COSTO: ~$0 adicional** (dentro del plan Hobby)

---

## 📚 Recursos

- [Railway Docs - Redis](https://docs.railway.app/databases/redis)
- [Celery Docs](https://docs.celeryq.dev/)
- [Django Celery Beat](https://django-celery-beat.readthedocs.io/)
- [Railway - Multiple Services](https://docs.railway.app/deploy/multiple-services)

---

**¿Listo para configurar?** Sigue los pasos en orden y avísame en qué paso estás! 🚀
