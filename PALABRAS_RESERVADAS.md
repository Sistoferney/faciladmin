# 🔒 Palabras Reservadas del Sistema

## ¿Qué son las palabras reservadas?

Son nombres que **NO se pueden usar** como nombre de negocio porque generarían conflicto con las URLs del sistema FacilAdmin.

---

## 📋 Lista Completa de Palabras Reservadas

### Administración y Sistema
- `admin` - Panel de administración de Django
- `login` - Página de inicio de sesión
- `logout` - Cerrar sesión
- `registro` - Página de registro
- `dashboard` - Panel de control

### APIs y Servicios
- `api` - Endpoints de API
- `static` - Archivos estáticos (CSS, JS, imágenes)
- `media` - Archivos subidos por usuarios

### Autenticación
- `accounts` - Cuentas de usuario
- `auth` - Autenticación
- `authentication` - Sistema de autenticación
- `usuarios` - Gestión de usuarios
- `users` - Usuarios

### Configuración
- `sistema` - Sistema
- `system` - Sistema
- `configuracion` - Configuración
- `config` - Configuración
- `settings` - Ajustes
- `superadmin` - Superadministrador
- `root` - Raíz del sistema
- `administrador` - Administrador

### Páginas del Landing
- `precios` - Página de precios
- `pricing` - Precios
- `contacto` - Contacto
- `contact` - Contacto
- `como-funciona` - Cómo funciona
- `about` - Acerca de
- `ayuda` - Ayuda
- `help` - Ayuda

### Legal
- `terminos` - Términos y condiciones
- `terms` - Términos
- `privacidad` - Política de privacidad
- `privacy` - Privacidad
- `legal` - Legal

### Soporte
- `soporte` - Soporte técnico
- `support` - Soporte

---

## ⚠️ ¿Qué pasa si intento usar una palabra reservada?

### Escenario 1: Registro desde el formulario web
Si intentas registrar un negocio llamado "Admin" o "Login":

```
❌ Error: El nombre "Admin" genera una URL reservada del sistema.
   Por favor elige otro nombre para tu negocio.
```

### Escenario 2: Creación desde Django Admin
Si un superadmin intenta crear un negocio con slug reservado:

```python
ValidationError: El nombre "admin" está reservado por el sistema.
```

### Escenario 3: El sistema modifica automáticamente
Si el nombre base colisiona con una palabra reservada, el sistema **agrega automáticamente un sufijo**:

| Nombre Original | Slug Generado | Resultado Final |
|----------------|---------------|-----------------|
| Admin | admin | admin-negocio |
| Login Spa | login-spa | login-spa-negocio |
| API Beauty | api-beauty | api-beauty-negocio |

---

## ✅ Nombres Válidos (Ejemplos)

Estos nombres **SÍ se pueden usar**:

- ✅ "Spa Patricia"
- ✅ "Salón Belleza María"
- ✅ "Barbería El Corte"
- ✅ "Admin Spa" (se convierte en `admin-spa-negocio`)
- ✅ "Beauty Admin" (se convierte en `beauty-admin`)
- ✅ "Spa & Relax"
- ✅ "Peluquería Central"

---

## 🛡️ Capas de Protección

FacilAdmin tiene **3 niveles de protección**:

### 1. Validación en el Formulario
```python
def clean_nombre_negocio(self):
    slug = slugify(nombre)
    if slug.lower() in SLUGS_RESERVADOS:
        raise forms.ValidationError('Nombre reservado')
```

### 2. Validación en el Modelo
```python
def clean(self):
    if self.slug.lower() in SLUGS_RESERVADOS:
        raise ValidationError('Slug reservado')
```

### 3. Modificación Automática en save()
```python
def save(self):
    if base_slug in SLUGS_RESERVADOS:
        base_slug = f"{base_slug}-negocio"
```

---

## 🔧 Cómo Agregar Más Palabras Reservadas

Si necesitas reservar más palabras, edita el archivo:

**`apps/negocios/models.py`**

```python
SLUGS_RESERVADOS = [
    # ... palabras existentes ...
    'nueva-palabra-reservada',
    'otro-slug-protegido',
]
```

---

## 📊 Ejemplos de URLs y Colisiones

### ❌ Lo que queremos EVITAR:

```
Negocio llamado "Admin":
  URL generada: http://midominio.com/admin/
  ⚠️ CONFLICTO con: Panel de Django Admin

Negocio llamado "Login":
  URL generada: http://midominio.com/login/
  ⚠️ CONFLICTO con: Página de inicio de sesión

Negocio llamado "API":
  URL generada: http://midominio.com/api/
  ⚠️ CONFLICTO con: Endpoints de API
```

### ✅ Lo que el sistema PERMITE:

```
Negocio llamado "Spa Patricia":
  URL generada: http://midominio.com/spa-patricia/
  ✅ Sin conflictos

Negocio llamado "Admin Spa":
  Intento de slug: admin-spa
  Contiene "admin" pero como prefijo de slug completo está OK
  URL generada: http://midominio.com/admin-spa/
  ✅ Sin conflictos (si no choca con SLUGS_RESERVADOS)

Negocio llamado "Admin" (exacto):
  Intento de slug: admin
  ⚠️ Reservado, se modifica automáticamente
  URL final: http://midominio.com/admin-negocio/
  ✅ Sistema lo corrige automáticamente
```

---

## 🧪 Probar la Validación

Ejecuta el script de prueba:

```bash
python test_slugs_reservados.py
```

Esto probará:
- Nombres prohibidos (deben ser rechazados)
- Nombres válidos (deben ser aceptados)
- Modificación automática de slugs conflictivos

---

## 📝 Notas Importantes

1. **Case Insensitive**: Las validaciones son insensibles a mayúsculas/minúsculas
   - "Admin", "ADMIN", "admin" → Todas bloqueadas

2. **Slugificación**: El nombre se convierte a slug antes de validar
   - "Mi Admin!" → `mi-admin` → Se valida contra SLUGS_RESERVADOS

3. **Protección Total**: Funciona en:
   - ✅ Formulario web de registro
   - ✅ Django Admin
   - ✅ Creación programática via código
   - ✅ Migraciones y fixtures

4. **Performance**: La lista de palabras reservadas está en memoria (es rápida)

---

## 🚨 Casos Especiales

### ¿Qué pasa si ya existe un negocio con slug reservado?

Si por alguna razón existe un negocio antiguo con slug "admin":

1. El sistema NO lo eliminará automáticamente
2. Nuevos negocios NO podrán usar ese slug
3. El negocio existente seguirá funcionando
4. Deberás cambiarlo manualmente si causa problemas

### ¿Puedo usar "adminspasalon" (todo junto)?

- Si `adminspasalon` NO está en SLUGS_RESERVADOS: ✅ SÍ
- Solo se bloquean las palabras EXACTAS de la lista
- "admin-spa", "spa-admin", etc. dependen de si están en la lista

---

## 📞 Soporte

Si tienes dudas sobre si un nombre es válido:
1. Intenta registrarlo desde el formulario
2. El sistema te dirá inmediatamente si está reservado
3. Elige un nombre alternativo

**Última actualización**: Mayo 2026
**Versión**: FacilAdmin v1.0
