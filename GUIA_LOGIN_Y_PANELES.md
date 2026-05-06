# Guía de Login y Paneles de Administración

## 🔐 Dos Sistemas de Autenticación

FacilAdmin tiene **dos sistemas de login separados** diseñados para diferentes tipos de usuarios:

---

## 1. Login para Administradores de Negocios ✅ (RECOMENDADO)

### URL de Login
```
http://127.0.0.1:8000/login/
```

### ¿Para quién?
- Dueños de spas, peluquerías, barberías
- Usuarios que registraron su negocio

### ¿A dónde redirige?
```
http://127.0.0.1:8000/{slug-del-negocio}/admin/
```
Ejemplo: `http://127.0.0.1:8000/spa-patty/admin/`

### Características
- ✅ Diseño moderno con degradado morado
- ✅ Panel personalizado e intuitivo
- ✅ Dashboard con estadísticas
- ✅ Vista previa de mini-página
- ✅ Gestión de servicios, citas, clientes, abonos
- ✅ Configuración del negocio
- ✅ No requiere conocimientos técnicos

### Cómo Acceder
1. Ve a http://127.0.0.1:8000/
2. Click en "Iniciar Sesión" en el navbar
3. Ingresa tu email y contraseña
4. Serás redirigido a tu panel personalizado

---

## 2. Login de Django Admin (Superadmins del Sistema)

### URL de Login
```
http://127.0.0.1:8000/admin/login/
```

### ¿Para quién?
- Superadministradores del sistema FacilAdmin
- Desarrolladores
- Personal técnico

### ¿A dónde redirige?
```
http://127.0.0.1:8000/admin/
```

### Características
- ✅ Diseño estándar de Django
- ✅ Acceso completo a todos los modelos
- ✅ Puede ver TODOS los negocios del sistema
- ✅ Herramientas avanzadas de administración
- ⚠️ Requiere conocimientos técnicos

### Cómo Acceder
1. Ve directamente a http://127.0.0.1:8000/admin/
2. Ingresa credenciales de superadmin
3. Accedes al panel de Django Admin

---

## 📊 Comparación de Paneles

| Característica | Panel Personalizado | Django Admin |
|----------------|---------------------|--------------|
| **URL** | `/{slug}/admin/` | `/admin/` |
| **Diseño** | Moderno, colorido | Estándar Django |
| **Usuarios** | Dueños de negocios | Superadmins |
| **Alcance** | Solo SU negocio | Todos los negocios |
| **Facilidad** | Muy fácil | Requiere conocimiento |
| **Dashboard** | Estadísticas visuales | Lista de modelos |
| **Vista previa** | Botón integrado | No disponible |

---

## 🎯 Rutas del Panel Personalizado

Una vez autenticado, el administrador del negocio tiene acceso a:

### Dashboard
```
/{slug}/admin/
```
- Estadísticas del día
- Citas de hoy
- Próximas citas
- Abonos pendientes
- Accesos rápidos

### Agenda de Citas
```
/{slug}/admin/agenda/
```
- Vista de citas por día
- Filtro por fecha
- Estadísticas del día
- Acciones: confirmar, completar, cancelar

### Gestión de Servicios
```
/{slug}/admin/servicios/
```
- Lista de servicios con imágenes
- Crear, editar, eliminar servicios
- Ver precio, duración, abonos

### Gestión de Clientes
```
/{slug}/admin/clientes/
```
- Lista completa de clientes
- Búsqueda por nombre, teléfono, email
- Estadísticas: citas, gastos, última visita

### Gestión de Abonos
```
/{slug}/admin/abonos/
```
- Filtros por estado
- Confirmar/rechazar abonos
- Ver comprobantes y referencias

### Configuración
```
/{slug}/admin/configuracion/
```
- Información del negocio
- Horarios de atención
- Configuración de abonos
- Personalización (colores)
- URL de mini-página

---

## 🔄 Flujo de Redirección Automática

### Cuando un usuario inicia sesión en `/login/`:

```
1. Django autentica credenciales
   ↓
2. Redirige a /dashboard/
   ↓
3. Vista redirect_after_login verifica:
   ├─ ¿Tiene negocio asociado? → /{slug}/admin/
   ├─ ¿Es superadmin sin negocio? → /admin/
   └─ ¿Otro caso? → /
```

### Configuración en settings.py:
```python
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'
```

---

## 🚀 URLs Principales del Sistema

### Landing y Páginas Públicas
- `/` - Landing page
- `/login/` - Login de administradores
- `/registro/` - Registro de nuevos negocios
- `/precios/` - Planes y precios
- `/como-funciona/` - Cómo funciona
- `/contacto/` - Contacto

### Panel de Administración Personalizado
- `/{slug}/admin/` - Dashboard
- `/{slug}/admin/servicios/` - Servicios
- `/{slug}/admin/agenda/` - Agenda
- `/{slug}/admin/clientes/` - Clientes
- `/{slug}/admin/abonos/` - Abonos
- `/{slug}/admin/configuracion/` - Configuración

### Mini-Página Pública (para clientes)
- `/{slug}/` - Vista pública del negocio
- `/{slug}/agendar/` - Formulario de reserva
- `/{slug}/confirmacion/{id}/` - Confirmación de cita

### Django Admin (solo superadmins)
- `/admin/` - Panel de Django Admin
- `/admin/login/` - Login de Django Admin

---

## ✅ Recomendaciones

### Para Dueños de Negocios:
1. **SIEMPRE usa:** http://127.0.0.1:8000/login/
2. **Guarda como favorito:** Tu panel personalizado `/{slug}/admin/`
3. **Comparte con clientes:** Tu mini-página `/{slug}/`

### Para Desarrolladores/Superadmins:
1. Usa: http://127.0.0.1:8000/admin/
2. Ten cuidado al modificar datos de negocios
3. Verifica permisos antes de hacer cambios globales

---

## 🔒 Seguridad y Permisos

### Administradores de Negocios:
- ✅ `is_staff = True` (puede acceder al admin)
- ❌ `is_superuser = False` (no puede ver otros negocios)
- ✅ 32 permisos específicos asignados
- ✅ Filtros en QuerySets limitan acceso a SU negocio

### Sistema de Filtrado:
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    # Si el usuario tiene un negocio asociado
    if hasattr(request.user, 'negocio'):
        qs = qs.filter(negocio=request.user.negocio)
    # Si no tiene negocio, es superadmin del sistema
    return qs
```

---

## 📞 Soporte

Si tienes problemas para iniciar sesión:
1. Verifica que estés usando la URL correcta: `/login/`
2. Asegúrate de tener permisos asignados
3. Cierra sesión completamente y vuelve a intentar
4. Verifica que tu negocio esté activo

---

**Última actualización:** Mayo 2026
**Versión del sistema:** FacilAdmin v1.0
