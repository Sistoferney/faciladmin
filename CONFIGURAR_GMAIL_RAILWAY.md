# Configurar Gmail en Railway - Paso a Paso

## 📧 Correo a Usar
**Email**: `seviciofaciladmin@gmail.com`

---

## 🔐 Paso 1: Crear App Password en Gmail

### 1.1 Acceder a tu Cuenta de Google

1. Ve a: **https://myaccount.google.com/apppasswords**
2. Inicia sesión con: `seviciofaciladmin@gmail.com`

### 1.2 Verificar Autenticación de 2 Factores

⚠️ **IMPORTANTE**: Para crear App Passwords, necesitas tener **Verificación en 2 pasos activada**.

**Si NO está activada**:
1. Ve a: https://myaccount.google.com/security
2. Busca "Verificación en 2 pasos"
3. Haz clic en "Activar"
4. Sigue los pasos (te pedirá tu número de teléfono)
5. Una vez activada, vuelve al paso 1.1

**Si YA está activada**:
- ✅ Continúa al siguiente paso

### 1.3 Crear la Contraseña de Aplicación

1. En https://myaccount.google.com/apppasswords
2. Verás un campo "Selecciona la app y el dispositivo"
3. En **"Selecciona la app"**: Elige **"Correo"**
4. En **"Selecciona el dispositivo"**: Elige **"Otro (nombre personalizado)"**
5. Escribe: **"FacilAdmin Railway"**
6. Haz clic en **"Generar"**

### 1.4 Copiar la Contraseña

Google te mostrará una contraseña de **16 caracteres** como esta:

```
abcd efgh ijkl mnop
```

⚠️ **IMPORTANTE**:
- ✅ **COPIA esta contraseña INMEDIATAMENTE**
- ✅ Solo se muestra UNA vez
- ✅ Guárdala temporalmente (la usaremos en el siguiente paso)

**Formato de la contraseña**:
- Puede tener espacios: `abcd efgh ijkl mnop`
- O sin espacios: `abcdefghijklmnop`
- **Ambos formatos funcionan** (Railway elimina espacios automáticamente)

---

## 🚀 Paso 2: Configurar Variables en Railway

### Opción A: Interfaz Web de Railway (Más Fácil)

1. **Abrir Railway**:
   - Ve a: https://railway.app/
   - Inicia sesión
   - Abre tu proyecto **FacilAdmin**

2. **Ir a Variables**:
   - Haz clic en tu servicio/aplicación
   - Haz clic en la pestaña **"Variables"**

3. **Agregar las Variables**:

   Haz clic en **"New Variable"** y agrega CADA una de estas:

   ```
   Variable Name: EMAIL_HOST
   Value: smtp.gmail.com
   ```

   ```
   Variable Name: EMAIL_PORT
   Value: 587
   ```

   ```
   Variable Name: EMAIL_USE_TLS
   Value: True
   ```

   ```
   Variable Name: EMAIL_HOST_USER
   Value: seviciofaciladmin@gmail.com
   ```

   ```
   Variable Name: EMAIL_HOST_PASSWORD
   Value: [PEGA AQUÍ LA CONTRASEÑA DE 16 CARACTERES]
   ```

4. **Guardar**:
   - Railway guardará automáticamente
   - La aplicación se reiniciará automáticamente

### Opción B: Railway CLI (Más Rápido si ya tienes CLI)

1. **Instalar Railway CLI** (si no lo tienes):
```bash
npm i -g @railway/cli
```

2. **Autenticarse**:
```bash
railway login
```

3. **Vincular proyecto**:
```bash
cd "e:\proyecto spa\faciladmin"
railway link
```

4. **Configurar variables** (REEMPLAZA `abcdefghijklmnop` con tu contraseña real):
```bash
railway variables set EMAIL_HOST=smtp.gmail.com
railway variables set EMAIL_PORT=587
railway variables set EMAIL_USE_TLS=True
railway variables set EMAIL_HOST_USER=seviciofaciladmin@gmail.com
railway variables set EMAIL_HOST_PASSWORD=abcdefghijklmnop
```

5. **Verificar**:
```bash
railway variables
```

Deberías ver:
```
EMAIL_HOST = smtp.gmail.com
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = seviciofaciladmin@gmail.com
EMAIL_HOST_PASSWORD = ****************
```

---

## ✅ Paso 3: Verificar que Funciona

### 3.1 Railway se Reiniciará Automáticamente

Después de configurar las variables, Railway reiniciará tu aplicación automáticamente (toma 1-2 minutos).

### 3.2 Verificar Logs

```bash
# Si usas CLI
railway logs

# O en la web
# Railway Dashboard > Tu Proyecto > Deployments > Ver logs
```

Busca errores relacionados con email. Si no hay errores, ¡está funcionando!

### 3.3 Probar el Sistema

1. **Ve a tu app en Railway**:
   ```
   https://tu-app.railway.app/login/
   ```

2. **Probar recuperación de contraseña**:
   - Intenta login con credenciales incorrectas 3 veces
   - Verás el botón naranja "Recuperar Contraseña"
   - Haz clic
   - Ingresa tu email personal (ej: `sistoferney@gmail.com`)
   - Haz clic en "Enviar"

3. **Revisar tu bandeja de entrada**:
   - Revisa tu correo personal
   - Deberías recibir el email en 5-30 segundos
   - **Revisa SPAM** si no lo ves en bandeja principal

4. **Email que recibirás**:
   ```
   De: seviciofaciladmin@gmail.com
   Para: tu-email@gmail.com
   Asunto: Recuperación de contraseña - FacilAdmin

   [Email HTML profesional con botón "Restablecer Mi Contraseña"]
   ```

---

## 🔍 Troubleshooting

### Problema 1: "App Passwords" no aparece

**Causa**: Verificación en 2 pasos no está activada

**Solución**:
1. Ve a: https://myaccount.google.com/security
2. Activa "Verificación en 2 pasos"
3. Espera 10 minutos
4. Vuelve a intentar crear App Password

### Problema 2: Email no llega

**Verificaciones**:

1. **Ver logs de Railway**:
```bash
railway logs | grep -i error
```

2. **Verificar variables**:
```bash
railway variables
```

Asegúrate que todas las 5 variables estén configuradas.

3. **Revisar SPAM**:
   - El primer email puede caer en spam
   - Márcalo como "No es spam"

4. **Verificar que la app se reinició**:
   - Railway Dashboard > Deployments
   - Debe haber un nuevo deployment después de configurar variables

### Problema 3: Error de autenticación

```
SMTPAuthenticationError: (535, b'5.7.8 Username and Password not accepted')
```

**Causas comunes**:
- ❌ App Password incorrecta
- ❌ Espacios extra en la contraseña
- ❌ Email incorrecto

**Solución**:
1. Genera una NUEVA App Password
2. Cópiala SIN espacios: `abcdefghijklmnop`
3. Vuelve a configurar en Railway:
```bash
railway variables set EMAIL_HOST_PASSWORD=nueva-password-sin-espacios
```

### Problema 4: "Less secure app access"

Si Gmail te pide habilitar "acceso de apps menos seguras":

❌ **NO lo habilites** - es inseguro

✅ **Usa App Passwords** - es el método correcto y seguro

---

## 📊 Comportamiento Esperado

### Flujo Completo en Producción:

```
Usuario olvida contraseña
      ↓
Hace 3 intentos fallidos
      ↓
Ve botón "Recuperar Contraseña"
      ↓
Ingresa email: sistoferney@gmail.com
      ↓
Sistema crea token en base de datos
      ↓
Django conecta con Gmail SMTP (smtp.gmail.com:587)
      ↓
Envía email desde: seviciofaciladmin@gmail.com
      ↓
Email llega a: sistoferney@gmail.com (5-30 segundos)
      ↓
Usuario abre email
      ↓
Ve email profesional con branding FacilAdmin
      ↓
Hace clic en "Restablecer Mi Contraseña"
      ↓
Redirigido a: https://tu-app.railway.app/recuperar-password/uuid/
      ↓
Ingresa nueva contraseña
      ↓
Token se marca como usado
      ↓
Login exitoso ✅
```

### Tiempos de Entrega:

- ⚡ **Rápido**: 5-15 segundos (90% de los casos)
- ⏱️ **Normal**: 15-60 segundos (9% de los casos)
- 🐌 **Lento**: 1-5 minutos (1% de los casos, revisa spam)

---

## 🔒 Seguridad

### ✅ Buenas Prácticas Implementadas:

1. **App Password** (NO contraseña de Gmail)
   - ✅ Más seguro
   - ✅ Puede revocarse sin cambiar contraseña de Gmail
   - ✅ Específica para FacilAdmin

2. **Variables de entorno en Railway**
   - ✅ Encriptadas
   - ✅ No están en el código
   - ✅ No están en Git

3. **Rate Limiting**
   - ✅ Solo 3 solicitudes de recuperación por hora por IP
   - ✅ Previene spam

4. **Tokens seguros**
   - ✅ UUID único
   - ✅ Expiran en 1 hora
   - ✅ Un solo uso

---

## 📧 Límites de Gmail

### Plan Gratuito:
- ✅ **500 emails por día**
- ✅ Suficiente para:
  - 16 recuperaciones de contraseña por hora
  - 500 usuarios olvidando contraseña por día
  - Más que suficiente para empezar

### ¿Qué pasa si excedes el límite?

Gmail te bloqueará temporalmente (24 horas) si envías más de 500 emails en un día.

**Soluciones si creces mucho**:
1. Migrar a SendGrid (100 emails/día gratis, $19.95/mes para más)
2. Migrar a AWS SES ($0.10 por 1,000 emails)
3. Google Workspace ($6/usuario/mes, 2,000 emails/día)

---

## ✅ Checklist Final

Antes de dar por terminado:

- [ ] Verificación en 2 pasos activada en Gmail
- [ ] App Password generada y copiada
- [ ] 5 variables configuradas en Railway:
  - [ ] EMAIL_HOST
  - [ ] EMAIL_PORT
  - [ ] EMAIL_USE_TLS
  - [ ] EMAIL_HOST_USER
  - [ ] EMAIL_HOST_PASSWORD
- [ ] Railway se reinició automáticamente
- [ ] Sin errores en logs de Railway
- [ ] Email de prueba enviado exitosamente
- [ ] Email recibido en bandeja (o spam)
- [ ] Flujo completo de recuperación probado

---

## 🎯 Resumen de Comandos

```bash
# Opción CLI (si prefieres terminal)
npm i -g @railway/cli
railway login
cd "e:\proyecto spa\faciladmin"
railway link

# Configurar variables (REEMPLAZA la password)
railway variables set EMAIL_HOST=smtp.gmail.com
railway variables set EMAIL_PORT=587
railway variables set EMAIL_USE_TLS=True
railway variables set EMAIL_HOST_USER=seviciofaciladmin@gmail.com
railway variables set EMAIL_HOST_PASSWORD=TU-APP-PASSWORD-DE-16-CARACTERES

# Verificar
railway variables

# Ver logs
railway logs
```

---

## 📞 Soporte

**Si tienes problemas**:
1. Revisa los logs: `railway logs`
2. Verifica las variables: `railway variables`
3. Asegúrate que App Password es correcta
4. Espera 10 minutos después de activar 2FA
5. Genera una nueva App Password si es necesario

---

**¡Listo para configurar!** 🚀

Sigue los pasos y en 5 minutos tendrás emails funcionando en producción.
