# Guía de PWA (Progressive Web App) - FacilAdmin

## ✅ Fase 1 Completada: PWA Básica

Tu aplicación FacilAdmin ahora es una **Progressive Web App** instalable tanto para dueños como para clientes.

---

## 🎯 ¿Qué se implementó?

### 1. **Manifest.json Dinámico**
- ✅ Manifest único para cada negocio (mini-página)
- ✅ Manifest único para panel admin
- ✅ Usa el logo del negocio como ícono
- ✅ Colores personalizados por negocio
- ✅ URLs:
  - Mini-página: `/{slug}/manifest.json`
  - Panel admin: `/{slug}/admin/manifest.json`

### 2. **Service Worker**
- ✅ Caché de assets estáticos
- ✅ Estrategia Network-First
- ✅ Funcionalidad offline básica
- ✅ Preparado para notificaciones push (Fase 2)
- ✅ Ubicación: `/static/js/sw.js`

### 3. **PWA Registration Script**
- ✅ Registro automático del Service Worker
- ✅ Detección de instalación
- ✅ Manejo del evento `beforeinstallprompt`
- ✅ Actualización automática del SW
- ✅ Ubicación: `/static/js/pwa-register.js`

### 4. **Meta Tags PWA**
- ✅ Meta tags en ambos templates (público y admin)
- ✅ Soporte para Android (Chrome, Edge)
- ✅ Soporte para iOS (Safari)
- ✅ Theme color personalizado por negocio
- ✅ Iconos y splash screens

### 5. **Banner de Instalación**
- ✅ Banner inteligente en mini-página
- ✅ Solo se muestra si la app NO está instalada
- ✅ Botón de instalación con un clic
- ✅ Mensaje motivador para clientes

---

## 🧪 Cómo Probar la PWA

### **Requisitos:**
- HTTPS habilitado (obligatorio para PWA)
- Navegador moderno (Chrome, Edge, Safari)
- Railway ya provee HTTPS automáticamente

### **Opción 1: Probar en Desktop (Chrome/Edge)**

1. **Iniciar el servidor:**
   ```bash
   python manage.py runserver
   ```

2. **Abrir Chrome/Edge en modo incógnito:**
   - Chrome: `Ctrl + Shift + N`
   - Edge: `Ctrl + Shift + P`

3. **Navegar a tu mini-página:**
   ```
   http://localhost:8000/{slug-del-negocio}/
   ```
   Por ejemplo: `http://localhost:8000/mi-spa/`

4. **Verificar instalabilidad:**
   - Abre DevTools: `F12`
   - Ve a la pestaña **Application** (Aplicación)
   - En el sidebar, selecciona **Manifest**
   - Verifica que aparezca el nombre, íconos y configuración del negocio

5. **Instalar la PWA:**
   - Busca el ícono de instalación en la barra de direcciones (➕)
   - O presiona `Ctrl + Shift + P` y busca "Instalar"
   - O haz clic en el banner que aparece arriba

6. **Verificar Service Worker:**
   - En DevTools, ve a **Application** → **Service Workers**
   - Verifica que el SW esté activo
   - Prueba ir offline y recargar (debería funcionar parcialmente)

### **Opción 2: Probar en Móvil (Android)**

1. **Desplegar a Railway:**
   ```bash
   git add .
   git commit -m "Implementar PWA básica"
   git push
   ```

2. **Esperar deployment en Railway** (~2-3 minutos)

3. **Abrir en Chrome móvil:**
   ```
   https://tu-dominio.up.railway.app/{slug}/
   ```

4. **Instalar:**
   - Aparecerá un banner automático: "Agregar a pantalla de inicio"
   - O desde el menú (⋮) → "Instalar app" o "Agregar a pantalla de inicio"

5. **Verificar instalación:**
   - Busca el ícono en el escritorio del teléfono
   - Ábrelo → Debería abrir en pantalla completa (sin barra del navegador)
   - Ve a Ajustes → Apps → Busca el nombre del negocio

### **Opción 3: Probar en iPhone (iOS/Safari)**

1. **Abrir en Safari:**
   ```
   https://tu-dominio.up.railway.app/{slug}/
   ```

2. **Instalar:**
   - Tap en el botón "Compartir" (cuadrado con flecha)
   - Scroll down → "Agregar a pantalla de inicio"
   - Confirmar

3. **Abrir desde pantalla de inicio:**
   - La app se abrirá en modo standalone

---

## 📱 Experiencia del Usuario

### **Para CLIENTES (mini-página):**

1. **Primera visita:**
   - Ve la mini-página normal
   - Aparece banner: "¡Instala nuestra app!"

2. **Después de instalar:**
   - Ícono del negocio en pantalla de inicio
   - Abrir → App en pantalla completa
   - Logo del negocio como splash screen
   - Puede agendar citas sin navegador

### **Para DUEÑOS (panel admin):**

1. **Acceder al panel:**
   ```
   /{slug}/admin/
   ```

2. **Instalar:**
   - Chrome mostrará opción de instalar
   - Se instala como app separada del cliente

3. **Uso:**
   - Gestiona todo desde app instalada
   - Notificaciones (cuando implementemos Fase 2)
   - Funciona parcialmente offline

---

## 🔍 Verificar que Funciona

### **Checklist PWA:**

**Manifest:**
- [ ] Navega a `/{slug}/manifest.json`
- [ ] Debe retornar JSON con nombre, íconos, colores
- [ ] Verifica que use el logo del negocio

**Service Worker:**
- [ ] DevTools → Application → Service Workers
- [ ] Estado: "activated and is running"
- [ ] Scope: "/"

**Instalabilidad:**
- [ ] Aparece ícono de instalación en navegador
- [ ] Banner de instalación visible (mini-página)
- [ ] Se puede instalar sin errores

**Offline:**
- [ ] Instala la app
- [ ] Activa modo avión
- [ ] Abre la app instalada
- [ ] Debe cargar (aunque sin datos dinámicos nuevos)

**Lighthouse Audit:**
- [ ] DevTools → Lighthouse
- [ ] Run audit (PWA category)
- [ ] Score debe ser > 90

---

## 🐛 Troubleshooting

### **"Service Worker no se registra"**
- Verifica que estés en HTTPS (o localhost)
- Revisa la consola por errores de JavaScript
- Verifica que `/static/js/sw.js` sea accesible

### **"No aparece opción de instalar"**
- Refresca con `Ctrl + Shift + R` (hard reload)
- Verifica que el manifest esté accesible
- Asegúrate de tener íconos válidos
- Prueba en modo incógnito

### **"Banner no aparece"**
- Solo aparece si la app NO está instalada
- Chrome requiere que el sitio cumpla criterios de PWA
- Revisa que `pwa-register.js` se cargue sin errores

### **"Error al cargar manifest"**
- Verifica que la URL `/{slug}/manifest.json` responda JSON válido
- Revisa que `color_primario` esté definido en el negocio
- Verifica que los archivos estáticos se sirvan correctamente

---

## 📊 Testing Local con HTTPS

Para probar PWA en local con HTTPS:

```bash
# Instalar mkcert (solo una vez)
# Windows (con Chocolatey):
choco install mkcert

# Generar certificado local
mkcert localhost 127.0.0.1 ::1

# Ejecutar Django con SSL
python manage.py runserver_plus --cert-file cert.pem --key-file key.pem
```

O usar **ngrok** para tunnel HTTPS:
```bash
ngrok http 8000
```

---

## 🚀 Próximos Pasos: Fase 2

La Fase 1 está completa. Cuando estés listo, implementaremos:

### **Fase 2: Notificaciones Push**
- [ ] Configurar VAPID keys
- [ ] Instalar `django-webpush`
- [ ] Registrar suscripciones push
- [ ] Crear sistema de notificaciones para dueños
- [ ] Crear sistema de recordatorios para clientes

### **Fase 3: Sistema de Recordatorios Inteligente**
- [ ] Celery para tareas programadas
- [ ] Enviar notificaciones 24h antes de cita
- [ ] Fallback a SMS si no tiene PWA instalada
- [ ] Panel de preferencias de notificaciones

### **Fase 4: SMS como Respaldo**
- [ ] Integrar Onurix o Twilio
- [ ] Enviar SMS solo si no responde a push
- [ ] Sistema híbrido automático

---

## 📚 Recursos

**Testing:**
- [PWA Builder](https://www.pwabuilder.com/) - Validar tu PWA
- [Lighthouse](https://developers.google.com/web/tools/lighthouse) - Audit PWA

**Documentación:**
- [MDN Web Docs - PWA](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps)
- [web.dev - PWA](https://web.dev/progressive-web-apps/)
- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)

---

## ✨ Resultado Final

**Antes:**
- ❌ Solo accesible vía navegador
- ❌ Sin notificaciones
- ❌ No funciona offline
- ❌ Clientes deben abrir navegador cada vez

**Después:**
- ✅ Instalable como app nativa
- ✅ Ícono en pantalla de inicio
- ✅ Splash screen personalizado
- ✅ Funciona parcialmente offline
- ✅ Preparado para notificaciones (Fase 2)
- ✅ Experiencia de app móvil
- ✅ **COSTO: $0 USD**

---

**¿Listo para probar?** Despliega a Railway y prueba instalar la app en tu celular! 📱
