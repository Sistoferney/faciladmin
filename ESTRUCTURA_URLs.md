# 📍 Estructura de URLs - FacilAdmin

## 🌐 Sistema Multi-Tenant Completo

FacilAdmin es un **sistema SaaS multi-tenant** donde:
- **Tú** eres el proveedor del servicio
- Cada **spa/peluquería** tiene su propia cuenta y mini página
- Cada **cliente** pertenece a un spa/peluquería específica

---

## 🎯 URLs Principales

### 1. Tu Sitio (Landing Page)

**URL Base**: `http://localhost:8000/`

| URL | Descripción | Vista |
|-----|-------------|-------|
| `/` | Landing page principal | Presenta el servicio FacilAdmin |
| `/registro/` | Registro de nuevos negocios | Spas/peluquerías se registran aquí |
| `/precios/` | Planes y precios | Información de planes |
| `/como-funciona/` | Cómo funciona el sistema | Tutorial explicativo |
| `/contacto/` | Página de contacto | Formulario de contacto |

**Funcionalidad**:
- Los dueños de spas/peluquerías visitan tu sitio
- Se registran y crean su cuenta
- Obtienen acceso al panel de administración

---

### 2. Panel de Administración

**URL**: `http://localhost:8000/admin/`

| Usuario | Acceso | Permisos |
|---------|--------|----------|
| **Super Admin** (TÚ) | Ve TODO | Gestiona todos los negocios del sistema |
| **Admin de Negocio** | Ve SU negocio | Solo gestiona su spa/peluquería |

**Módulos Disponibles**:
- ✅ Negocios
- ✅ Servicios
- ✅ Clientes
- ✅ Citas
- ✅ Abonos
- ✅ Promociones
- ✅ Notificaciones
- ✅ Bloqueos de Agenda
- ✅ Reportes

---

### 3. Mini Páginas de Cada Negocio (URLs Públicas)

**Patrón**: `http://localhost:8000/{slug-del-negocio}/`

Cada negocio registrado obtiene su propia mini página con URL única.

#### Ejemplo: Spa Relax
```
http://localhost:8000/spa-relax/
http://localhost:8000/spa-relax/agendar/
http://localhost:8000/spa-relax/confirmacion/123/
```

#### URLs por Negocio:

| URL | Descripción | Público |
|-----|-------------|---------|
| `/{slug}/` | Mini página principal | ✅ Sí |
| `/{slug}/agendar/` | Formulario de reserva | ✅ Sí |
| `/{slug}/confirmacion/{id}/` | Confirmación de cita | ✅ Sí |
| `/{slug}/api/disponibilidad/` | API de horarios | ✅ Sí |

**Características**:
- 🎨 Personalizable (colores, logo)
- 📱 100% Responsive
- 🔗 URL compartible
- 📅 Sistema de reservas integrado
- 💳 Información de abonos

---

## 📊 Ejemplos Reales

### Ejemplo 1: Tú (Proveedor del Servicio)

1. **Tu Landing**: `http://localhost:8000/`
2. **Tu Admin**: `http://localhost:8000/admin/`
   - Username: tu_email@ejemplo.com
   - Ves TODOS los negocios registrados

### Ejemplo 2: Spa Relax (Cliente Tuyo)

1. **Se registra en**: `http://localhost:8000/registro/`
   - Crea cuenta
   - Configura su negocio
   - Obtiene slug: `spa-relax`

2. **Su Admin**: `http://localhost:8000/admin/`
   - Username: admin@sparelax.com
   - Ve SOLO su spa

3. **Su Mini Página**: `http://localhost:8000/spa-relax/`
   - La comparte con sus clientes
   - Sus clientes agendan citas aquí

### Ejemplo 3: María (Cliente del Spa Relax)

1. **Visita**: `http://localhost:8000/spa-relax/`
2. **Reserva**: `http://localhost:8000/spa-relax/agendar/`
   - Llena formulario
   - Selecciona servicio y fecha
   - Recibe confirmación

3. **No necesita cuenta**: Solo su teléfono
   - El sistema la identifica por teléfono
   - Se crea perfil automáticamente

---

## 🔄 Flujos Completos

### Flujo 1: Registrar un Nuevo Negocio

```
Usuario visita → http://localhost:8000/
       ↓
Click "Prueba Gratis" → http://localhost:8000/registro/
       ↓
Llena formulario (datos + negocio)
       ↓
Se crea:
  - Usuario administrador
  - Negocio con slug único
       ↓
Redirección → http://localhost:8000/admin/
       ↓
Puede configurar servicios, horarios, etc.
```

### Flujo 2: Cliente Agenda Cita

```
Cliente recibe enlace → http://localhost:8000/spa-relax/
       ↓
Ve servicios y precios
       ↓
Click "Agendar" → http://localhost:8000/spa-relax/agendar/
       ↓
Llena formulario:
  - Nombre, teléfono
  - Selecciona servicio
  - Elige fecha/hora
       ↓
Sistema:
  - Crea/recupera cliente por teléfono
  - Crea cita
  - Envía notificación WhatsApp
       ↓
Confirmación → http://localhost:8000/spa-relax/confirmacion/123/
       ↓
Si requiere abono → Muestra datos bancarios
```

### Flujo 3: Admin Gestiona Citas

```
Admin inicia sesión → http://localhost:8000/admin/
       ↓
Ve "Citas" → Lista de citas pendientes
       ↓
Si hay abono pendiente:
  - Cliente transfirió dinero
  - Admin confirma en "Abonos"
  - Sistema actualiza cita a "Confirmada"
  - Notifica cliente automáticamente
       ↓
24h antes de cita:
  - Sistema envía recordatorio automático
```

---

## 🗂️ Estructura de Datos

### Jerarquía:

```
FacilAdmin (Tu Plataforma)
├── Usuario 1 (Super Admin - TÚ)
│
├── Negocio 1: Spa Relax
│   ├── Admin: admin@sparelax.com
│   ├── Slug: spa-relax
│   ├── Servicios: [Masaje, Facial, ...]
│   ├── Clientes: [María, Juan, ...]
│   └── Citas: [...]
│
├── Negocio 2: Barbería El Corte
│   ├── Admin: admin@elcorte.com
│   ├── Slug: barberia-el-corte
│   ├── Servicios: [Corte, Barba, ...]
│   ├── Clientes: [Carlos, Luis, ...]
│   └── Citas: [...]
│
└── Negocio N...
```

---

## 🚀 URLs de Desarrollo

Durante desarrollo (localhost):

```
Landing:        http://localhost:8000/
Registro:       http://localhost:8000/registro/
Admin:          http://localhost:8000/admin/
Mini Página:    http://localhost:8000/{slug}/
```

---

## 🌍 URLs de Producción

Cuando despliegues (ejemplo):

```
Landing:        https://faciladmin.com/
Registro:       https://faciladmin.com/registro/
Admin:          https://faciladmin.com/admin/
Mini Página:    https://faciladmin.com/{slug}/
```

Ejemplos de mini páginas:
- https://faciladmin.com/spa-relax/
- https://faciladmin.com/barberia-el-corte/
- https://faciladmin.com/salon-belleza-maria/

---

## ✅ Próximos Pasos

1. **Reiniciar el servidor**:
   ```bash
   python manage.py runserver
   ```

2. **Probar Landing Page**:
   - Visita: http://localhost:8000/
   - Explora las páginas

3. **Registrar un Negocio de Prueba**:
   - Ve a: http://localhost:8000/registro/
   - Crea un negocio nuevo
   - Accede al admin

4. **Configurar el Negocio**:
   - Agrega servicios
   - Personaliza colores/logo
   - Configura horarios

5. **Visitar Mini Página**:
   - http://localhost:8000/{tu-slug}/
   - Probar agendar cita

6. **Gestionar desde Admin**:
   - Ver citas
   - Confirmar abonos
   - Enviar promociones

---

## 📚 Documentación Relacionada

- [GUIA_USO.md](GUIA_USO.md) - Guía completa de uso
- [README.md](README.md) - Información general
- [INSTALACION.md](INSTALACION.md) - Instalación del sistema

---

¡Tu sistema multi-tenant está listo! 🎉
