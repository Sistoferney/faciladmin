# Configurar Resend para FacilAdmin

## ¿Qué es Resend?

Resend es un servicio moderno de email transaccional que usa **HTTPS** (puerto 443) en lugar de SMTP (puerto 587).

**Ventajas sobre Gmail SMTP:**
- ✅ **Funciona en Railway sin plan Pro** (usa puerto 443, nunca bloqueado)
- ✅ **Gratis hasta 3,000 emails/mes** (vs 100/día de SendGrid)
- ✅ **Sin worker timeouts** (API rápida vs SMTP lento)
- ✅ **Deliverability excelente** (emails no van a spam)
- ✅ **Dashboard moderno** para ver emails enviados

---

## Paso 1: Crear Cuenta en Resend (GRATIS)

1. Ve a: https://resend.com/signup
2. Regístrate con tu email
3. Verifica tu email
4. ¡Listo! Ya tienes 3,000 emails/mes gratis

---

## Paso 2: Verificar Dominio (Opcional pero Recomendado)

### Opción A: Usar dominio personalizado (Recomendado)

Si tienes un dominio (ej: `faciladmin.com`):

1. En Resend Dashboard: **Domains** → **Add Domain**
2. Ingresa tu dominio: `faciladmin.com`
3. Agrega los registros DNS que Resend te muestra:
   ```
   Tipo: TXT
   Nombre: @
   Valor: [valor que te da Resend]

   Tipo: CNAME
   Nombre: resend._domainkey
   Valor: [valor que te da Resend]
   ```
4. Espera 5-10 minutos para que se verifique
5. Una vez verificado, podrás enviar desde: `noreply@faciladmin.com`

### Opción B: Usar dominio de prueba (Desarrollo/Testing)

Resend te da un dominio de prueba: `onboarding.resend.dev`
- Solo puedes enviar a emails que agregues a la lista
- Perfecto para desarrollo inicial
- **NO recomendado para producción**

---

## Paso 3: Crear API Key

1. En Resend Dashboard: **API Keys** → **Create API Key**
2. Nombre: `FacilAdmin Production`
3. Permiso: **Full Access** (o "Sending access" si solo envías emails)
4. Copia el API Key (se muestra solo una vez):
   ```
   re_xxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
5. ¡Guárdalo! Lo necesitarás en el siguiente paso

---

## Paso 4: Configurar Variables en Railway

Opción A - Desde CLI (reemplaza con tu API Key):
```bash
cd "e:\proyecto spa\faciladmin"
railway variables set RESEND_API_KEY="re_xxxxxxxxxxxxxxxxxxxxxxxxxx" --service faciladmin
railway variables set DEFAULT_FROM_EMAIL="noreply@faciladmin.com" --service faciladmin
```

Opción B - Desde Dashboard Web:
1. Ve a: https://railway.app/
2. Proyecto: **faciladmin**
3. Servicio: **faciladmin**
4. Pestaña: **Variables**
5. Agrega/Edita las siguientes variables:

```bash
# IMPORTANTE: Reemplaza con tu API Key real
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxxxx

# Email desde el cual se enviarán los correos
# Usa tu dominio verificado o el dominio de prueba
DEFAULT_FROM_EMAIL=noreply@faciladmin.com

# O si usas dominio de prueba:
# DEFAULT_FROM_EMAIL=onboarding@resend.dev
```

---

## Paso 5: Verificar Deployment

Después de configurar las variables, Railway hará **redeploy automático**.

Espera 1-2 minutos y verifica:

```bash
railway logs --service faciladmin
```

Busca:
- ✅ NO debe haber errores de "RESEND_API_KEY"
- ✅ NO debe haber "WORKER TIMEOUT"
- ✅ Los workers deben iniciar normalmente

---

## Paso 6: Probar Recuperación de Contraseña

1. Ve a: https://faciladmin-production.up.railway.app/login/
2. Haz clic en **"¿Olvidaste tu contraseña?"**
3. Ingresa un email registrado en el sistema
4. Haz clic en **"Enviar enlace de recuperación"**

**Resultado esperado:**
- ✅ La página responde **inmediatamente** (sin congelarse)
- ✅ Muestra mensaje de éxito
- ✅ El email llega en **menos de 5 segundos**
- ✅ Email tiene formato profesional con HTML

**Si el email no llega:**
- Revisa la carpeta de **spam**
- Verifica que el email esté registrado en FacilAdmin
- Si usas dominio de prueba, asegúrate de haber agregado el email a la lista permitida

---

## Configuración Completa de Variables

Variables **obligatorias** en Railway:

```bash
# Resend (Nuevo)
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxxxx
DEFAULT_FROM_EMAIL=noreply@faciladmin.com

# Django (Ya existentes - NO cambiar)
SECRET_KEY=iijaspg-_3*@#q*u8lu19c$9c%0)t$b44h$xc%4!ib*s^r@jpk
DEBUG=False
DJANGO_SETTINGS_MODULE=config.settings.production

# Database (Ya existente - NO cambiar)
DATABASE_URL=postgresql://postgres:...

# Cloudinary (Ya existente - NO cambiar)
CLOUDINARY_CLOUD_NAME=dyjz4o32i
CLOUDINARY_API_KEY=398541256631776
CLOUDINARY_API_SECRET=5WuCHn_8Ff1kyhKJj5UPbPOFEFo

# VAPID (Ya existente - NO cambiar)
VAPID_PUBLIC_KEY=...
VAPID_PRIVATE_KEY=...
VAPID_ADMIN_EMAIL=admin@faciladmin.com

# Gunicorn (Ya configurado)
GUNICORN_TIMEOUT=120
```

Variables **obsoletas** (puedes eliminarlas ya que no se usan con Resend):
```bash
# YA NO NECESARIAS - SMTP Gmail
EMAIL_HOST=smtp.gmail.com          ← Puedes eliminar
EMAIL_PORT=587                      ← Puedes eliminar
EMAIL_USE_TLS=True                  ← Puedes eliminar
EMAIL_HOST_USER=...                 ← Puedes eliminar
EMAIL_HOST_PASSWORD=...             ← Puedes eliminar
EMAIL_TIMEOUT=10                    ← Puedes eliminar
```

---

## Verificar Email en Resend Dashboard

1. Ve a: https://resend.com/emails
2. Deberías ver el email que acabas de enviar
3. Puedes ver:
   - Estado (Delivered/Bounced/etc)
   - Destinatario
   - Hora de envío
   - Contenido del email

---

## Solución de Problemas

### Error: "RESEND_API_KEY no está configurada"

**Solución:**
```bash
railway variables set RESEND_API_KEY="re_xxxxxxxxx" --service faciladmin
```

### Error: "DEFAULT_FROM_EMAIL no verificado"

**Causa:** Estás usando un email desde un dominio no verificado.

**Solución:**
1. Verifica tu dominio en Resend Dashboard, O
2. Usa el dominio de prueba: `onboarding@resend.dev`

### Los emails van a spam

**Soluciones:**
1. **Verifica tu dominio** con registros DNS (SPF, DKIM)
2. **Configura DMARC** en tu dominio
3. Resend configura automáticamente SPF/DKIM si verificas el dominio

### Error: "Invalid API key"

**Causa:** El API Key es incorrecto o expiró.

**Solución:**
1. Ve a Resend Dashboard → API Keys
2. Crea un nuevo API Key
3. Actualiza la variable en Railway

---

## Comandos Útiles

Ver variables actuales:
```bash
railway variables --service faciladmin | grep -E "(RESEND|DEFAULT_FROM)"
```

Ver logs en tiempo real:
```bash
railway logs --service faciladmin --follow
```

Verificar deployment:
```bash
railway status
```

Probar email localmente:
```bash
python manage.py shell

from django.core.mail import send_mail
send_mail(
    'Test desde Django',
    'Este es un email de prueba.',
    'noreply@faciladmin.com',
    ['tu-email@gmail.com'],
    fail_silently=False,
)
```

---

## Comparación: SMTP vs Resend

| Característica | Gmail SMTP | Resend API |
|----------------|------------|------------|
| **Puerto** | 587 (bloqueado en Railway) | 443 (HTTPS, nunca bloqueado) |
| **Plan Railway requerido** | Pro ($20/mes) | Gratis / Trial / Hobby |
| **Velocidad** | Lenta (1-5s por email) | Rápida (<500ms) |
| **Timeouts** | Común (bloquea workers) | Nunca |
| **Emails gratis/mes** | Ilimitados (con Gmail) | 3,000 |
| **Deliverability** | Buena | Excelente |
| **Dashboard** | No | Sí |
| **Configuración** | Compleja (App Password) | Simple (API Key) |

---

## Estado Actual

- ✅ Backend de Resend implementado
- ✅ Configuración de producción actualizada
- ✅ EMAIL_TIMEOUT configurado (10s)
- ⏳ Pendiente: Crear cuenta en Resend
- ⏳ Pendiente: Configurar RESEND_API_KEY en Railway
- ⏳ Pendiente: Probar en producción

---

## Próximos Pasos

1. **Crear cuenta en Resend**: https://resend.com/signup
2. **Verificar dominio** (opcional pero recomendado)
3. **Crear API Key**
4. **Configurar en Railway**:
   ```bash
   railway variables set RESEND_API_KEY="re_xxxxxxxxx" --service faciladmin
   railway variables set DEFAULT_FROM_EMAIL="noreply@tudominio.com" --service faciladmin
   ```
5. **Probar recuperación de contraseña** en producción
6. **(Opcional) Eliminar variables SMTP antiguas** de Railway

---

## Costos

- **Resend Gratis**: 3,000 emails/mes, 100 emails/día
- **Resend Pro**: $20/mes → 50,000 emails/mes

Para FacilAdmin, el plan gratis es **más que suficiente**:
- 3,000 emails/mes = 100 emails/día
- Recuperación de contraseña + notificaciones de citas
- Muy poco probable que superes este límite

---

## Soporte

- Documentación Resend: https://resend.com/docs/introduction
- SDK Python: https://github.com/resend/resend-python
- Railway Docs: https://docs.railway.com/

¡Listo! Con esto tendrás un sistema de email moderno, rápido y confiable sin pagar por Railway Pro.
