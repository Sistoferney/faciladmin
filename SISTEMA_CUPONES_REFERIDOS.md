# Sistema de Cupones y Referidos - FacilAdmin

## Resumen del Sistema

Hemos implementado un sistema completo de cupones y referidos que permite a los admins de negocios obtener meses gratis de suscripción al referir otros negocios.

## Características Principales

### 1. Sistema de Cupones Simplificado

- **Un solo tipo**: Todos los cupones otorgan 1 mes gratis (30 días)
- **Sin cupones en el registro**: El registro siempre otorga 120 días gratis automáticamente
- **Cupones post-trial**: Los cupones se usan DESPUÉS del período de prueba de 120 días
- **Asignación específica**: Los cupones pueden asignarse a un negocio específico
- **Control de uso**: Cada cupón solo puede canjearse una vez

### 2. Programa de Referidos

#### Mecánica

1. El admin de negocio debe ingresar 3 números telefónicos de negocios YA registrados en FacilAdmin
2. Cada número telefónico solo puede ser referido una vez (no puede estar en la lista de otro referidor)
3. Los 3 negocios referidos deben estar activos
4. Una vez completados los 3 referidos activos, el admin puede generar un cupón mensual
5. Cada mes que los 3 referidos sigan activos, se genera un nuevo cupón automáticamente

#### Validaciones

- ✅ El negocio debe estar registrado en FacilAdmin
- ✅ El teléfono no puede estar ya referido por otro admin
- ✅ No puede referirse a sí mismo
- ✅ El negocio debe estar activo (esta_activo=True)
- ✅ Solo puede generar 1 cupón por mes

## Modelos Implementados

### ProgramaReferidos

```python
class ProgramaReferidos(models.Model):
    negocio = models.OneToOneField('negocios.Negocio', ...)
    negocio_referido_1 = models.ForeignKey('negocios.Negocio', ...)
    negocio_referido_2 = models.ForeignKey('negocios.Negocio', ...)
    negocio_referido_3 = models.ForeignKey('negocios.Negocio', ...)
    activo = models.BooleanField(default=False)
    fecha_ultimo_cupon = models.DateTimeField(null=True)
    total_cupones_generados = models.IntegerField(default=0)
```

**Métodos principales:**
- `referidos_activos()`: Cuenta cuántos referidos están activos
- `cumple_requisitos()`: Verifica si tiene 3 referidos activos
- `puede_generar_cupon()`: Verifica si puede generar cupón este mes
- `generar_cupon_mensual()`: Genera el cupón y lo asigna al negocio
- `agregar_referido(telefono)`: Agrega un negocio referido validando todas las reglas

### Cupon (Actualizado)

```python
class Cupon(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    meses_gratis = models.IntegerField(default=1, editable=False)
    activo = models.BooleanField(default=True)
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_expiracion = models.DateTimeField(null=True)
    negocio_asignado = models.ForeignKey('negocios.Negocio', ...)  # NUEVO
    usado = models.BooleanField(default=False)  # NUEVO
    fecha_uso = models.DateTimeField(null=True)  # NUEVO
```

**Métodos principales:**
- `puede_canjear(negocio)`: Valida si el negocio puede canjear el cupón
- `canjear(negocio)`: Canjea el cupón y extiende 30 días la suscripción

## Vistas Implementadas

### 1. Dashboard de Referidos
**URL**: `/programa-referidos/`
**Vista**: `programa_referidos_dashboard`

Muestra:
- Progreso actual (X/3 referidos)
- Lista de referidos con su estado (activo/inactivo)
- Formularios para agregar nuevos referidos
- Botón para generar cupón mensual (si cumple requisitos)
- Total de cupones generados

### 2. Agregar Referido (AJAX)
**URL**: `/programa-referidos/agregar/`
**Vista**: `agregar_referido_ajax`
**Método**: POST

Parámetros:
- `telefono`: Número telefónico del negocio a referir

Respuesta JSON:
```json
{
    "success": true,
    "mensaje": "Negocio agregado como referido",
    "referidos_activos": 3,
    "cumple_requisitos": true
}
```

### 3. Generar Cupón Mensual
**URL**: `/programa-referidos/generar-cupon/`
**Vista**: `generar_cupon_referidos`
**Método**: POST

Genera el cupón mensual si cumple requisitos y envía email al admin con el código.

### 4. Canjear Cupón
**URL**: `/canjear-cupon/`
**Vista**: `canjear_cupon`

Formulario para ingresar código de cupón y canjearlo, extendiendo 30 días la suscripción automáticamente.

## Admin de Django

### ProgramaReferidosAdmin

**Características:**
- Lista de todos los programas con badges de estado
- Filtros por activo/inactivo y fecha de creación
- Búsqueda por nombre de negocio
- raw_id_fields para selección eficiente de negocios

**Acciones disponibles:**
1. **Actualizar estado de referidos**: Verifica que los 3 referidos sigan activos
2. **Generar cupones mensuales**: Genera cupones para todos los seleccionados que cumplan requisitos

## Comando de Management

### generar_cupones_mensuales

```bash
# Ejecutar en modo simulación
python manage.py generar_cupones_mensuales --dry-run

# Ejecutar y generar cupones reales
python manage.py generar_cupones_mensuales
```

**Funcionalidad:**
- Busca todos los programas activos
- Actualiza el estado de cada programa (verifica que referidos sigan activos)
- Genera cupón para los que cumplan requisitos
- Envía email con el código del cupón
- Muestra resumen detallado de la ejecución

**Programación sugerida (crontab):**
```bash
# Ejecutar el primer día de cada mes a las 00:00
0 0 1 * * cd /path/to/faciladmin && ./venv/bin/python manage.py generar_cupones_mensuales
```

## Flujo de Uso Completo

### Para el Admin de Negocio:

1. **Inscripción en el programa**
   - Ir a `/programa-referidos/`
   - Ingresar 3 números telefónicos de negocios registrados
   - Sistema valida que cada número sea válido

2. **Generación del primer cupón**
   - Una vez completados los 3 referidos
   - Hacer clic en "Generar Mi Cupón Mensual"
   - Recibe email con el código

3. **Canje del cupón**
   - Ir a `/canjear-cupon/`
   - Ingresar código recibido
   - Su suscripción se extiende automáticamente 30 días

4. **Cupones mensuales automáticos**
   - Cada mes, si los 3 referidos siguen activos
   - El sistema genera un nuevo cupón automáticamente
   - Recibe email con el nuevo código

### Para el Superusuario:

1. **Monitoreo en Django Admin**
   - Ver todos los programas de referidos
   - Ver quién cumple requisitos
   - Ver total de cupones generados

2. **Generación manual de cupones**
   - Seleccionar programas en el admin
   - Usar acción "Generar cupones mensuales"

3. **Ejecución mensual del comando**
   - Configurar cron job para ejecutar automáticamente
   - O ejecutar manualmente: `python manage.py generar_cupones_mensuales`

## Archivos Modificados/Creados

### Modelos
- ✅ `apps/suscripciones/models.py` - Agregado ProgramaReferidos
- ✅ `apps/suscripciones/models.py` - Actualizado Cupon (simplificado)
- ✅ `apps/suscripciones/models.py` - Actualizado UsoCupon

### Admin
- ✅ `apps/suscripciones/admin.py` - Agregado ProgramaReferidosAdmin
- ✅ `apps/suscripciones/admin.py` - Actualizado CuponAdmin

### Vistas
- ✅ `apps/suscripciones/views.py` - Agregado programa_referidos_dashboard
- ✅ `apps/suscripciones/views.py` - Agregado agregar_referido_ajax
- ✅ `apps/suscripciones/views.py` - Agregado generar_cupon_referidos
- ✅ `apps/suscripciones/views.py` - Agregado canjear_cupon
- ✅ `apps/suscripciones/views.py` - Simplificado registro_negocio (sin cupones)

### URLs
- ✅ `apps/suscripciones/urls.py` - Agregadas rutas del programa de referidos

### Templates
- ✅ `templates/suscripciones/programa_referidos.html` - Dashboard del programa
- ✅ `templates/suscripciones/canjear_cupon.html` - Formulario de canje
- ✅ `templates/suscripciones/registro.html` - Removido campo de cupón
- ✅ `templates/suscripciones/activar_cuenta.html` - Removida lógica de cupones

### Comandos
- ✅ `apps/suscripciones/management/commands/generar_cupones_mensuales.py`

### Migraciones
- ✅ `apps/suscripciones/migrations/0002_programareferidos.py`

## Próximos Pasos Sugeridos

1. ✅ **Integrar en el Dashboard Principal**
   - Agregar widget mostrando progreso del programa de referidos
   - Mostrar cupones disponibles para canjear

2. ⏳ **Notificaciones**
   - Notificar cuando un referido se desactiva
   - Recordatorio para generar cupón mensual

3. ⏳ **Analytics**
   - Dashboard de métricas del programa de referidos
   - Tasa de conversión de referidos
   - Cupones más utilizados

4. ⏳ **Integración con Wompi**
   - Botón de pago para cuando termine el trial
   - Aplicar cupones como descuento en checkout

## Configuración de Producción

### Variables de Entorno Necesarias

```env
# Email (ya configurado)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_password
DEFAULT_FROM_EMAIL=noreply@faciladmin.com
```

### Cron Job Mensual

```bash
# Agregar a crontab en el servidor
crontab -e

# Ejecutar el primer día de cada mes a las 00:00
0 0 1 * * cd /ruta/a/faciladmin && /ruta/a/faciladmin/venv/bin/python manage.py generar_cupones_mensuales >> /var/log/cupones_mensuales.log 2>&1
```

## Testing

### Pruebas Manuales Sugeridas

1. **Registrar negocio de prueba**
   - Ir a `/registro/`
   - Completar registro (sin cupón)
   - Verificar que recibe 120 días gratis

2. **Inscribirse en programa de referidos**
   - Ir a `/programa-referidos/`
   - Agregar 3 números telefónicos válidos
   - Verificar validaciones

3. **Generar cupón**
   - Completar 3 referidos
   - Hacer clic en "Generar cupón"
   - Verificar recepción de email

4. **Canjear cupón**
   - Ir a `/canjear-cupon/`
   - Ingresar código recibido
   - Verificar que suscripción se extendió

5. **Comando mensual**
   - Ejecutar: `python manage.py generar_cupones_mensuales --dry-run`
   - Verificar salida del comando
   - Ejecutar sin --dry-run
   - Verificar emails enviados

---

**Implementado por**: Claude
**Fecha**: Septiembre 2026
**Versión**: 1.0
