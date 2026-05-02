# 📖 Guía de Uso - FacilAdmin

## 🎯 Opción Rápida: Datos de Ejemplo

Si quieres **probar el sistema rápidamente**, ejecuta este script que crea datos de ejemplo:

```bash
python crear_datos_ejemplo.py
```

Esto creará automáticamente:
- ✅ Un negocio de ejemplo configurado
- ✅ 5 servicios (corte, tinte, masaje, facial, manicure)
- ✅ 4 clientes de prueba
- ✅ 3 citas de ejemplo
- ✅ Configuración de horarios

**Luego ve al admin** (http://localhost:8000/admin) y explora todo.

---

## 📋 Configuración Manual Paso a Paso

### 1. Crear tu Negocio

**Ruta**: Admin → Negocios → Agregar negocio

**Campos obligatorios**:
- Administrador: Tu usuario
- Nombre: Nombre de tu spa/peluquería
- Tipo: Spa, Peluquería, Barbería, etc.
- Teléfono: Número de contacto
- Slug: Se genera automáticamente (es tu URL única)

**Configuración de Abonos** (Importante):
```
¿Requiere abono? → ✅ Sí (si quieres pagos anticipados)
Porcentaje de abono → 50% (o el que prefieras)
Banco → Nombre de tu banco
Número de cuenta → Tu cuenta
CLABE → Tu CLABE interbancaria
Titular → Nombre del titular
```

**Personalización**:
- Color primario: #007bff (azul) o el de tu marca
- Color secundario: #6c757d (gris)
- Logo: Sube tu logo
- Imagen de portada: Para la mini página

---

### 2. Configurar Horarios

**Ruta**: Admin → Negocios → Tu negocio → Editar

Al editar tu negocio, verás al final una tabla inline para configurar horarios por día.

**Ejemplo**:
```
Lunes:    09:00 - 19:00 ✅ Abierto
Martes:   09:00 - 19:00 ✅ Abierto
Miércoles: 09:00 - 19:00 ✅ Abierto
Jueves:   09:00 - 19:00 ✅ Abierto
Viernes:  09:00 - 20:00 ✅ Abierto
Sábado:   10:00 - 18:00 ✅ Abierto
Domingo:  ❌ Cerrado
```

---

### 3. Crear Servicios

**Ruta**: Admin → Servicios → Agregar servicio

**Campos importantes**:

| Campo | Ejemplo | Descripción |
|-------|---------|-------------|
| Nombre | Corte de Cabello | Nombre del servicio |
| Precio | 150.00 | Precio en pesos |
| Duración (minutos) | 30 | Cuánto dura el servicio |
| Frecuencia sugerida (días) | 30 | Cada cuántos días se recomienda repetir |
| Activo | ✅ | Si se puede reservar |
| Orden | 1 | Orden de visualización |

**Frecuencia sugerida** - Ejemplos:
- Corte de cabello: 30 días
- Tinte: 45 días
- Masaje: 15 días
- Manicure: 14 días
- Facial: 20 días

💡 **Tip**: La frecuencia sugerida es clave para el sistema de fidelización. El sistema enviará recordatorios automáticos basándose en este valor.

---

### 4. Gestión de Clientes

**Ruta**: Admin → Clientes

#### Crear Cliente Manual:
1. Clic en "Agregar cliente"
2. Llena: Nombre, Teléfono (único), Email
3. Tipo de cliente:
   - **Nuevo**: Primera vez
   - **Frecuente**: 3+ citas
   - **Inactivo**: 90+ días sin visitar

#### Cliente Automático:
Los clientes se crean automáticamente cuando:
- Agendan desde la mini página web
- Se registra una cita con un teléfono nuevo

**Preferencias importantes**:
- ✅ Acepta WhatsApp: Para notificaciones
- ✅ Acepta promociones: Para campañas
- ✅ Acepta SMS/Email: Canales alternativos

---

### 5. Sistema de Citas

**Ruta**: Admin → Citas → Agregar cita

#### Campos:

**Básicos**:
- Cliente
- Servicio
- Fecha y hora
- Duración (se copia del servicio)

**Estados de Cita**:
- 🟡 **Pendiente de abono**: Esperando confirmación de pago
- 🟢 **Confirmada**: Abono confirmado, cita asegurada
- 🔵 **Completada**: Cita realizada
- 🔴 **Cancelada**: Cita cancelada
- ⚫ **No asistió**: Cliente no se presentó

**Origen**:
- 🌐 **Reserva Web**: Cliente agendó desde mini página
- ✋ **Registro Manual**: Administrador creó la cita
- 🚶 **Sin reserva previa**: Walk-in (cliente llegó sin avisar)

#### Flujo de Abonos:

```
1. Cliente agenda → Estado: "Pendiente de abono"
2. Cliente transfiere dinero
3. Admin confirma pago → Estado: "Confirmada"
4. Cliente asiste → Estado: "Completada"
```

**Acciones masivas**:
En la lista de citas puedes:
- ✅ Confirmar abonos (seleccionar varias y confirmar)
- ✅ Marcar como completadas
- ❌ Cancelar citas

---

### 6. Sistema de Abonos

**Ruta**: Admin → Abonos

Cuando una cita requiere abono, se crea automáticamente un registro.

**Estados**:
- 🟡 Pendiente: Esperando pago
- 🟢 Confirmado: Admin validó el pago
- 🔴 Rechazado: Admin rechazó el pago
- ⚫ Vencido: Pasó la fecha límite

**Flujo**:
1. Cliente hace transferencia
2. Sube comprobante (o te lo envía)
3. Tú confirmas en Admin → Abonos
4. Sistema notifica al cliente automáticamente

---

### 7. Promociones y Campañas

**Ruta**: Admin → Promociones → Agregar promoción

**Segmentos disponibles**:
- 👥 **Todos los clientes**
- 🆕 **Clientes nuevos**: Solo tipo "nuevo"
- ⭐ **Clientes frecuentes**: Tipo "frecuente"
- 😴 **Clientes inactivos**: Más de 90 días sin visitar

**Ejemplo de Promoción**:
```
Nombre: 20% Descuento Septiembre
Descripción: Promoción de bienvenida
Mensaje:
  ¡Hola {nombre}!

  Este mes tenemos 20% de descuento en todos
  nuestros servicios. ¡No te lo pierdas!

  Agenda ya: {negocio}

Segmento: Clientes inactivos
Estado: Borrador
```

**Para enviar**:
1. Selecciona la promoción
2. Acciones → "Enviar promociones seleccionadas"
3. Se envía por WhatsApp/SMS/Email según preferencias

---

### 8. Bloqueo de Agenda

**Ruta**: Admin → Bloqueos de agenda → Agregar bloqueo

**Uso**: Bloquear horarios cuando:
- Tienes cita personal
- Mantenimiento del local
- Vacaciones
- Evento especial

**Campos**:
- Fecha y hora de inicio
- Fecha y hora de fin
- Motivo interno (solo tú lo ves)

💡 Los clientes NO verán el motivo, solo que ese horario no está disponible.

---

### 9. Reportes

**Ruta**: Admin → Reportes

(Funcionalidad en construcción - próximamente disponible en API)

Podrás ver:
- 📊 Total de citas del período
- 💰 Ingresos estimados
- 👥 Clientes recurrentes
- 📉 Horarios con baja ocupación
- 📈 Servicios más solicitados
- ❌ Tasa de cancelación

---

## 🎨 Mini Página del Negocio

Cada negocio tiene una URL única:

```
http://localhost:8000/tu-negocio-slug
```

**Características**:
- ✅ 100% Responsive
- ✅ Colores personalizables
- ✅ Logo y portada
- ✅ Catálogo de servicios
- ✅ Sistema de reservas integrado
- ✅ Información de contacto
- ✅ Redes sociales

(Vista pública próximamente)

---

## 🔔 Sistema de Notificaciones

### Tipos de Notificaciones Automáticas:

1. **Confirmación de cita** (RF-18)
   - Se envía al agendar
   - Incluye: fecha, hora, servicio, ubicación
   - Si requiere abono, incluye datos bancarios

2. **Recordatorio 24h antes** (RF-28)
   - Tarea automática (Celery)
   - Se envía un día antes de la cita

3. **Recordatorio de abono** (RF-56)
   - 48h antes del límite
   - 24h antes del límite

4. **Confirmación de abono** (RF-57)
   - Cuando admin confirma el pago

5. **Sugerencia de próxima cita** (RF-29, RF-30)
   - Basada en frecuencia del servicio
   - Tarea automática

6. **Reactivación de clientes** (RF-32)
   - Para clientes inactivos
   - Tarea automática semanal

### Canales (prioridad):
1. WhatsApp (si acepta)
2. SMS (si no tiene WhatsApp)
3. Email (último recurso)

---

## 🤖 Tareas Automáticas (Celery)

Para que funcionen las notificaciones automáticas, necesitas ejecutar Celery:

**Terminal 1** - Worker:
```bash
celery -A config worker -l info
```

**Terminal 2** - Beat (tareas programadas):
```bash
celery -A config beat -l info
```

**Tareas programadas**:
- ⏰ 09:00 - Verificar abonos pendientes
- ⏰ 10:00 - Enviar recordatorios de citas
- ⏰ 11:00 - Sugerir próximas citas
- ⏰ Lunes 08:00 - Identificar clientes inactivos

---

## 💡 Tips y Buenas Prácticas

### Para Servicios:
- Define bien la frecuencia sugerida
- Mantén precios actualizados
- Desactiva servicios temporales en lugar de borrarlos

### Para Clientes:
- El sistema actualiza automáticamente el tipo (nuevo/frecuente/inactivo)
- Un teléfono solo puede usarse una vez por negocio
- El historial nunca se borra, solo se desactiva el cliente

### Para Citas:
- No se pueden solapar citas en el mismo horario (RN-02)
- Las citas con abono requieren mínimo 2 días de anticipación (RF-55)
- Usa "Completada" para que cuente en estadísticas

### Para Abonos:
- Confirma o rechaza rápido para buena experiencia
- El sistema notifica automáticamente al confirmar
- Puedes agregar notas internas

---

## ❓ Preguntas Frecuentes

**¿Cómo cambio mi contraseña?**
Admin → Usuarios Administradores → Tu usuario → Cambiar contraseña

**¿Puedo tener varios administradores?**
Sí, crea más usuarios en "Usuarios Administradores"

**¿Cómo veo las notificaciones enviadas?**
Admin → Notificaciones

**¿Los clientes necesitan crear cuenta?**
No, solo necesitan su teléfono para agendar

**¿Puedo exportar mis datos?**
Próximamente. Por ahora usa el admin de Django.

---

## 🆘 Soporte

Si necesitas ayuda, revisa:
- [README.md](README.md)
- [INSTALACION.md](INSTALACION.md)
- [INICIO_RAPIDO.md](INICIO_RAPIDO.md)

---

¡Disfruta FacilAdmin! 🎉
