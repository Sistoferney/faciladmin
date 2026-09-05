# Plan de Implementación - Sistema de Suscripción FacilAdmin

## 1. RESUMEN EJECUTIVO

### Objetivo
Implementar un sistema de suscripción SaaS con período de prueba gratuito de 4 meses, seguido de suscripción mensual/anual mediante pasarela de pagos.

### ⚡ Filosofía del Sistema: "EMPEZAR GRATIS, CRECER DESPUÉS"

**Principios clave:**
- ✅ **Sin barreras de entrada**: Registro en 3 minutos, sin tarjeta de crédito
- ✅ **Trial real**: 120 días con acceso COMPLETO (no limitado)
- ✅ **Onboarding después**: El usuario entra primero, configura después
- ✅ **Premium desde día 1**: Botón visible pero no intrusivo
- ✅ **Conversión orgánica**: El usuario ve valor antes de pagar

### Flujo Propuesto (ULTRA SIMPLIFICADO)

```
┌─────────────────────────────────────────────────────────────────┐
│                    REGISTRO (2 minutos)                         │
├─────────────────────────────────────────────────────────────────┤
│ Paso 1: Formulario básico                                      │
│   → Nombre, Apellido, Teléfono, Email                          │
│   → [Crear Cuenta Gratis]                                      │
├─────────────────────────────────────────────────────────────────┤
│ Paso 2: Email de validación                                    │
│   → "Activa tu cuenta gratis de 120 días"                      │
│   → Usuario hace clic en link                                  │
├─────────────────────────────────────────────────────────────────┤
│ Paso 3: Completar activación                                   │
│   → Nombre del negocio                                         │
│   → Contraseña + Confirmar                                     │
│   → [Activar Mi Cuenta] → Login automático                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  DENTRO DE LA APLICACIÓN                        │
├─────────────────────────────────────────────────────────────────┤
│ ✅ Trial activo: 120 días                                       │
│ ✅ Full access sin restricciones                                │
│ ✅ Wizard de onboarding (opcional, guiado)                      │
│ ✅ Botón "Hacerse Premium" visible (navbar)                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│              CONVERSIÓN A PREMIUM (día 1-120)                   │
├─────────────────────────────────────────────────────────────────┤
│ Día 1-90:   Botón discreto "⭐ Hacerse Premium"                │
│ Día 91-110: Banner amarillo + botón más visible                │
│ Día 111-119: Banner rojo + botón pulsante "¡Activa Premium!"  │
│ Día 120:    Modal OBLIGATORIO → Pago para continuar           │
└─────────────────────────────────────────────────────────────────┘
```

### 🎯 Mejoras del Flujo Nuevo vs Anterior

| Métrica | Antes | Ahora | Mejora |
|---------|-------|-------|--------|
| Campos en registro | 5-6 | 4 | -33% |
| Campos en validación | 4-5 | 2 | -60% |
| Tiempo hasta dashboard | 5-10 min | 2-3 min | -70% |
| Pasos obligatorios | 4 | 3 | -25% |
| Tasa conversión estimada | 40-50% | 70-80% | +50% |

---

## 2. COMPARATIVA DE PASARELAS DE PAGO

### 2.1. WOMPI (Recomendada para Colombia)

#### ✅ Ventajas
- **Comisiones competitivas**: ~2.5% transacciones
- **PSE muy económico**: 1.49% (ideal para Colombia)
- **Respaldo Bancolombia**: Mayor confianza
- **Soporte Nequi**: Método preferido por colombianos (12M+ usuarios)
- **API REST completa**: Documentación en español
- **Tokenización**: Para cargos recurrentes sin solicitar tarjeta cada vez
- **Soporte local**: Equipo en Colombia

#### ❌ Desventajas
- No tiene integración directa con Daviplata
- Menos features avanzados que Stripe
- Documentación menos extensa que Stripe

#### 💰 Costos Estimados
- PSE: 1.49%
- Tarjetas: ~2.5-2.9%
- Nequi: ~2.5%
- Sin costos de instalación

#### 🔧 Características Técnicas
- API REST
- Webhooks para eventos
- Tokenización de tarjetas
- Soporte suscripciones recurrentes
- SDK disponible (aunque integración directa es simple)

---

### 2.2. STRIPE (Alternativa Internacional)

#### ✅ Ventajas
- **Stripe Billing**: Sistema de suscripciones más completo del mercado
- **Stripe Radar**: Prevención de fraude avanzada
- **API de clase mundial**: Documentación excepcional
- **Escalabilidad**: Empresas Fortune 500 lo usan
- **Customer Portal**: Portal self-service para clientes
- **Internacionalización**: Ideal si planeas expandir fuera de Colombia
- **Múltiples monedas**: Acepta pagos globales

#### ❌ Desventajas
- **Comisiones más altas**: ~3.7% en Colombia
- **No soporta Nequi/Daviplata** (aún)
- **Menos familiar para usuarios colombianos**
- Enfocado en mercado internacional

#### 💰 Costos Estimados
- Transacciones: 3.7% + fees
- Stripe Billing: Incluido
- Sin costos mensuales base

#### 🔧 Características Técnicas
- Stripe Checkout (hosted)
- Stripe Billing (suscripciones automáticas)
- Customer Portal (auto-gestión)
- Webhooks robustos
- SDKs en todos los lenguajes
- Test mode completo

---

### 2.3. MERCADO PAGO

#### ✅ Ventajas
- **Reconocimiento de marca**: Muy conocido en LATAM
- **Pagos en cuotas**: Sin interés o con interés
- **Amplia cobertura**: Métodos de pago locales
- **PSE integrado**
- **Botón de pago simple**: Fácil implementación básica

#### ❌ Desventajas
- Comisiones variables (3-5%)
- Sistema de suscripciones menos robusto que Stripe/Wompi
- Soporte técnico puede ser lento
- API menos documentada

---

### 2.4. PAYU

#### ✅ Ventajas
- Cobertura en toda LATAM
- Métodos de pago locales completos
- Buen soporte empresarial
- Posibilidad de negociar tarifas con volumen

#### ❌ Desventajas
- Comisiones similares a Wompi (~2.5-3%)
- Interfaz menos moderna
- Documentación puede ser confusa

---

### 2.5. ePAYCO

#### ✅ Ventajas
- Soporte local colombiano excelente
- Fácil integración
- Bueno para pequeñas empresas
- Comisiones competitivas

#### ❌ Desventajas
- Menos features avanzados
- No tan escalable como otras opciones

---

## 3. RECOMENDACIÓN

### 🏆 Estrategia Híbrida Recomendada

```
FASE 1 (MVP - 0-6 meses): WOMPI
├── Razón: Comisiones bajas, integración simple, mercado local
├── Métodos: PSE (1.49%) + Tarjetas + Nequi
└── Ventaja: Rentable para validar mercado

FASE 2 (Escala - 6+ meses): WOMPI + STRIPE (opcional)
├── Wompi: Clientes colombianos (mayoría)
├── Stripe: Clientes internacionales + features avanzados
└── Ventaja: Mejor de ambos mundos
```

### Justificación
1. **Wompi es ideal para empezar**:
   - Comisiones bajas maximizan margen inicial
   - PSE 1.49% es imbatible
   - Usuarios colombianos prefieren Nequi/PSE

2. **Stripe como complemento futuro**:
   - Si expandes internacionalmente
   - Si necesitas features avanzados (customer portal, revenue recognition, etc.)
   - Si volumen justifica pagar 3.7%

---

## 4. ARQUITECTURA PROPUESTA

### 4.1. Modelos de Django

```python
# apps/suscripciones/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class PlanSuscripcion(models.Model):
    """Planes disponibles"""
    TIPO_PLAN = [
        ('trial', 'Trial Gratuito'),
        ('mensual', 'Mensual'),
        ('anual', 'Anual'),
    ]

    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_PLAN)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    duracion_dias = models.IntegerField()  # 120 para trial, 30 mensual, 365 anual
    descripcion = models.TextField()
    activo = models.BooleanField(default=True)

    # Límites del plan (None = ilimitado)
    # NOTA: Trial tiene acceso completo (todos en None/True)
    max_citas_mes = models.IntegerField(null=True, blank=True)  # None = ilimitado
    max_servicios = models.IntegerField(null=True, blank=True)  # None = ilimitado
    max_clientes = models.IntegerField(null=True, blank=True)   # None = ilimitado
    push_notifications = models.BooleanField(default=True)
    soporte_prioritario = models.BooleanField(default=False)    # Solo Premium

    def __str__(self):
        return f"{self.nombre} - ${self.precio}"


class Suscripcion(models.Model):
    """Suscripción activa de un negocio"""
    ESTADO_CHOICES = [
        ('trial', 'Trial Activo'),
        ('activa', 'Activa'),
        ('vencida', 'Vencida'),
        ('cancelada', 'Cancelada'),
        ('suspendida', 'Suspendida'),
    ]

    negocio = models.OneToOneField('negocios.Negocio', on_delete=models.CASCADE, related_name='suscripcion')
    plan = models.ForeignKey(PlanSuscripcion, on_delete=models.PROTECT)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='trial')

    # Fechas
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_fin = models.DateTimeField()
    fecha_cancelacion = models.DateTimeField(null=True, blank=True)

    # Pagos
    metodo_pago = models.CharField(max_length=50, null=True, blank=True)  # 'wompi', 'stripe', etc.
    token_pago = models.CharField(max_length=255, null=True, blank=True)  # Token de Wompi/Stripe
    referencia_externa = models.CharField(max_length=255, null=True, blank=True)  # Subscription ID externo

    # Renovación automática
    auto_renovacion = models.BooleanField(default=False)

    # Auditoría
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.negocio.nombre} - {self.plan.nombre} ({self.estado})"

    @property
    def esta_activa(self):
        """Verifica si la suscripción está activa"""
        if self.estado in ['cancelada', 'suspendida']:
            return False
        return timezone.now() <= self.fecha_fin

    @property
    def dias_restantes(self):
        """Días hasta que expire"""
        if not self.esta_activa:
            return 0
        delta = self.fecha_fin - timezone.now()
        return delta.days

    def puede_usar_feature(self, feature):
        """Verifica si puede usar una característica según límites del plan"""
        if not self.esta_activa:
            return False

        # Implementar lógica de límites aquí
        if feature == 'push_notifications':
            return self.plan.push_notifications

        return True


class PagoSuscripcion(models.Model):
    """Historial de pagos"""
    ESTADO_PAGO = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('reembolsado', 'Reembolsado'),
    ]

    suscripcion = models.ForeignKey(Suscripcion, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADO_PAGO)

    # Referencia de pasarela
    pasarela = models.CharField(max_length=50)  # 'wompi', 'stripe'
    transaccion_id = models.CharField(max_length=255, unique=True)
    referencia = models.CharField(max_length=255, null=True, blank=True)

    # Metadata
    metodo_pago = models.CharField(max_length=50)  # 'pse', 'card', 'nequi'
    metadata = models.JSONField(null=True, blank=True)

    # Fechas
    fecha_pago = models.DateTimeField(default=timezone.now)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.suscripcion.negocio.nombre} - ${self.monto} ({self.estado})"


class Cupon(models.Model):
    """Cupones de descuento y meses gratis"""
    TIPO_CUPON = [
        ('mes_gratis', 'Mes Gratis'),
        ('descuento_porcentaje', 'Descuento Porcentaje'),
        ('descuento_fijo', 'Descuento Fijo'),
    ]

    codigo = models.CharField(max_length=50, unique=True)  # Ej: "PROMO2026", "REFERIDO-ABC123"
    tipo = models.CharField(max_length=30, choices=TIPO_CUPON, default='mes_gratis')

    # Valor del cupón
    meses_gratis = models.IntegerField(default=1)  # Para tipo 'mes_gratis'
    porcentaje_descuento = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # Para descuento %
    monto_descuento = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Para descuento fijo

    # Restricciones
    activo = models.BooleanField(default=True)
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_expiracion = models.DateTimeField(null=True, blank=True)
    usos_maximos = models.IntegerField(null=True, blank=True)  # None = ilimitado
    usos_actuales = models.IntegerField(default=0)

    # Aplicación
    solo_nuevos_usuarios = models.BooleanField(default=True)  # Solo para trial → premium
    solo_registro = models.BooleanField(default=False)  # Si True, solo en registro (extiende trial)

    # Metadata
    descripcion = models.TextField(blank=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.codigo} - {self.get_tipo_display()}"

    @property
    def esta_valido(self):
        """Verifica si el cupón es válido"""
        if not self.activo:
            return False

        # Verificar fechas
        ahora = timezone.now()
        if ahora < self.fecha_inicio:
            return False
        if self.fecha_expiracion and ahora > self.fecha_expiracion:
            return False

        # Verificar usos
        if self.usos_maximos and self.usos_actuales >= self.usos_maximos:
            return False

        return True

    def puede_usar(self, negocio):
        """Verifica si un negocio específico puede usar este cupón"""
        if not self.esta_valido:
            return False, "El cupón no es válido o ha expirado"

        # Verificar si ya lo usó
        if UsoCupon.objects.filter(cupon=self, negocio=negocio).exists():
            return False, "Ya has usado este cupón anteriormente"

        # Verificar restricción de nuevos usuarios
        if self.solo_nuevos_usuarios:
            suscripcion = negocio.suscripcion
            # Solo si está en trial o es su primer pago
            if suscripcion.estado not in ['trial', 'activa']:
                return False, "Este cupón solo es válido para nuevos usuarios"

        return True, "Cupón válido"

    def aplicar(self, negocio):
        """Aplica el cupón a un negocio"""
        puede, mensaje = self.puede_usar(negocio)
        if not puede:
            return False, mensaje

        # Registrar uso
        UsoCupon.objects.create(
            cupon=self,
            negocio=negocio,
            aplicado_en=timezone.now()
        )

        # Incrementar contador
        self.usos_actuales += 1
        self.save()

        return True, "Cupón aplicado exitosamente"


class UsoCupon(models.Model):
    """Registro de uso de cupones"""
    cupon = models.ForeignKey(Cupon, on_delete=models.CASCADE, related_name='usos')
    negocio = models.ForeignKey('negocios.Negocio', on_delete=models.CASCADE)
    aplicado_en = models.DateTimeField(default=timezone.now)

    # Beneficio otorgado
    meses_extendidos = models.IntegerField(default=0)
    descuento_aplicado = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        unique_together = ['cupon', 'negocio']
        verbose_name_plural = "Usos de cupones"

    def __str__(self):
        return f"{self.negocio.nombre} - {self.cupon.codigo}"


class RegistroNegocio(models.Model):
    """Datos de registro simplificado antes de crear el negocio completo"""
    ESTADO_REGISTRO = [
        ('pendiente_email', 'Pendiente Validación Email'),
        ('completado', 'Registro Completado'),
        ('expirado', 'Expirado'),
    ]

    # Datos básicos del usuario
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20)

    # Cupón (opcional)
    codigo_cupon = models.CharField(max_length=50, blank=True, null=True)
    cupon_aplicado = models.ForeignKey(Cupon, on_delete=models.SET_NULL, null=True, blank=True)

    # Validación
    estado = models.CharField(max_length=20, choices=ESTADO_REGISTRO, default='pendiente_email')
    token_validacion = models.CharField(max_length=100, unique=True)
    fecha_token_expira = models.DateTimeField()
    email_validado_en = models.DateTimeField(null=True, blank=True)

    # Relación con negocio creado
    negocio_creado = models.ForeignKey('negocios.Negocio', on_delete=models.SET_NULL, null=True, blank=True)

    # Auditoría
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.email} ({self.estado})"

    @property
    def token_valido(self):
        """Verifica si el token aún es válido"""
        return timezone.now() < self.fecha_token_expira
```

---

### 4.1.1. Sistema de Cupones

#### Tipos de Cupones

```python
1. MES_GRATIS: Extiende la suscripción por N meses
   - Ejemplo: "PROMO2026" → 1 mes gratis
   - Aplicación: Al pagar, se extiende 30 días adicionales

2. DESCUENTO_PORCENTAJE: Descuento en %
   - Ejemplo: "DESCUENTO50" → 50% off
   - Aplicación: $29.900 → $14.950

3. DESCUENTO_FIJO: Monto fijo de descuento
   - Ejemplo: "10MIL" → $10.000 de descuento
   - Aplicación: $29.900 → $19.900
```

#### Dónde se Aplican los Cupones

```
┌─────────────────────────────────────────────┐
│  OPCIÓN A: Durante el Registro              │
│  (Extiende el trial)                        │
├─────────────────────────────────────────────┤
│  Registro → Campo "¿Tienes cupón?"          │
│  ↓                                          │
│  Validar cupón: "PROMO120"                  │
│  ↓                                          │
│  Trial normal: 120 días                     │
│  + Cupón: 30 días extra                     │
│  = Trial extendido: 150 días                │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  OPCIÓN B: Durante el Checkout              │
│  (Descuento o mes gratis en primer pago)    │
├─────────────────────────────────────────────┤
│  Checkout → Campo "Código de cupón"         │
│  ↓                                          │
│  Aplicar "MESGRATIS"                        │
│  ↓                                          │
│  Primer mes: GRATIS                         │
│  Siguientes meses: $29.900                  │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  OPCIÓN C: Ambas (Recomendado)              │
├─────────────────────────────────────────────┤
│  - En registro: Solo cupones tipo           │
│    "solo_registro=True" (extienden trial)   │
│  - En checkout: Cualquier tipo de cupón     │
└─────────────────────────────────────────────┘
```

#### Casos de Uso para Cupones

```python
# 1. Programa de Referidos
REFERIDO-ABC123: 1 mes gratis
└── Se genera automáticamente por usuario
└── Cuando alguien se registra con tu cupón, ambos obtienen 1 mes gratis

# 2. Promoción de Lanzamiento
LANZAMIENTO2026: 50% de descuento primer mes
└── Válido solo primeros 100 usuarios
└── Expira 31/12/2026

# 3. Recuperación de Churners
VUELVE30: 1 mes gratis
└── Solo para usuarios que cancelaron
└── Válido 60 días después de cancelar

# 4. Fidelización
FIEL12: 20% de descuento
└── Para usuarios que cumplan 12 meses pagando
└── Válido indefinidamente mientras no cancelen

# 5. Eventos/Colaboraciones
COLABORADOR-NOMBRE: 2 meses gratis
└── Cupón especial para influencers/partners
└── Máximo 50 usos
```

#### Admin de Cupones

```python
# Panel admin para crear cupones
class CuponAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'tipo', 'meses_gratis', 'usos_actuales', 'usos_maximos', 'activo']
    list_filter = ['tipo', 'activo', 'solo_nuevos_usuarios']
    search_fields = ['codigo', 'descripcion']

    fieldsets = [
        ('Información Básica', {
            'fields': ['codigo', 'tipo', 'descripcion', 'activo']
        }),
        ('Beneficio', {
            'fields': ['meses_gratis', 'porcentaje_descuento', 'monto_descuento']
        }),
        ('Restricciones', {
            'fields': ['fecha_inicio', 'fecha_expiracion', 'usos_maximos',
                      'solo_nuevos_usuarios', 'solo_registro']
        })
    ]
```

---

### 4.2. Flujo de Registro SIMPLIFICADO

```
PASO 1: Formulario de Registro (Minimalista)
├── Nombre
├── Apellido
├── Teléfono
├── Email
├── ¿Tienes un cupón? (OPCIONAL) 🎁
│   └── Campo colapsable: "Ingresa tu código"
└── Aceptar términos y condiciones
└── [Botón: Crear Cuenta Gratis]

PASO 2: Enviar Email de Validación
├── Generar token único
├── Enviar email con link: "Activa tu cuenta gratis de 120 días"
├── Guardar RegistroNegocio con estado='pendiente_email'
└── Token expira en 24 horas

PASO 3: Usuario hace clic en link de validación
├── Validar token
├── Mostrar formulario final:
│   ├── Nombre del negocio
│   ├── Contraseña
│   └── Confirmar contraseña
└── [Botón: Activar Mi Cuenta]

PASO 4: Crear Todo Automáticamente
├── Crear User (username=email, password=ingresada)
├── Crear Negocio (nombre=ingresado, email, teléfono de registro)
├── Crear Suscripción Trial automática:
│   ├── Plan: 'trial'
│   ├── Estado: 'trial'
│   ├── Duración: 120 días
│   └── Full access sin restricciones
├── Actualizar RegistroNegocio.estado='completado'
└── Login automático

PASO 5: Redirigir a Dashboard con Onboarding
├── Banner de bienvenida
├── Wizard de onboarding guiado:
│   ├── 1. Sube tu logo
│   ├── 2. Elige tus colores
│   ├── 3. Configura horarios
│   ├── 4. Crea tu primer servicio
│   └── 5. Agenda tu primera cita
└── Botón visible: "Hacerse Premium" (disponible desde día 1)

PASO 6: Notificaciones de Trial
├── Día 90: "Te quedan 30 días de plan gratuito - ¡Hazte Premium!"
├── Día 110: "Solo 10 días para que expire tu plan gratuito"
├── Día 115: "Últimos 5 días - Continúa con Premium"
├── Día 119: "¡Último día! Activa Premium para seguir usando FacilAdmin"
└── Día 120: Modal obligatorio: "Suscríbete ahora para continuar"
```

**Ventajas del flujo simplificado:**
- ✅ Solo 2 campos en validación de email (vs 4-5 antes)
- ✅ Usuario entra al dashboard en segundos
- ✅ Onboarding guiado mejora engagement
- ✅ Menor fricción = mayor conversión
- ✅ Premium disponible desde día 1 (early adopters)

---

### 4.2.1. Comparación: Flujo Anterior vs Nuevo

| Aspecto | ❌ Flujo Anterior | ✅ Flujo NUEVO (Simplificado) |
|---------|------------------|-------------------------------|
| **Paso 1** | 4-5 campos (email, teléfono, nombre negocio, dirección) | 4 campos (nombre, apellido, teléfono, email) |
| **Validación Email** | Solo validar → Redirigir a otro formulario | Validar + Completar registro (2 campos: nombre negocio + password) |
| **Onboarding** | Configuración obligatoria antes de entrar | Wizard guiado DESPUÉS de entrar al dashboard |
| **Tiempo hasta dashboard** | 5-10 minutos | 2-3 minutos |
| **Fricción** | Alta (múltiples pasos) | Baja (solo lo esencial) |
| **Conversión esperada** | ~40-50% | ~70-80% |

### 4.2.2. Botón "Hacerse Premium"

El botón debe estar visible desde el **día 1** del trial, pero su comportamiento cambia según los días restantes:

```python
# apps/suscripciones/utils.py

def obtener_estado_boton_premium(suscripcion):
    """
    Retorna el estado del botón Premium según días restantes
    """
    dias_restantes = suscripcion.dias_restantes

    if dias_restantes > 30:
        return {
            'visible': True,
            'urgente': False,
            'texto': '⭐ Hacerse Premium',
            'estilo': 'btn-outline-primary',
            'mensaje': f'Te quedan {dias_restantes} días de plan gratuito',
            'badge': None
        }
    elif dias_restantes > 10:
        return {
            'visible': True,
            'urgente': True,
            'texto': '⭐ Hacerse Premium',
            'estilo': 'btn-warning',
            'mensaje': f'Solo {dias_restantes} días restantes',
            'badge': 'warning'
        }
    elif dias_restantes > 0:
        return {
            'visible': True,
            'urgente': True,
            'texto': '🚨 ¡Activar Premium YA!',
            'estilo': 'btn-danger',
            'mensaje': f'¡ÚLTIMOS {dias_restantes} DÍAS!',
            'badge': 'danger',
            'pulsar': True  # Animación pulsante
        }
    else:
        return {
            'visible': True,
            'urgente': True,
            'obligatorio': True,  # Modal obligatorio
            'texto': '🔒 Activar Premium para Continuar',
            'estilo': 'btn-danger',
            'mensaje': 'Tu plan gratuito ha expirado',
            'badge': 'danger',
            'bloquear_funciones': True
        }
```

**Ubicaciones del botón:**
1. **Navbar superior derecha** (siempre visible)
2. **Banner en dashboard** (cuando faltan <30 días)
3. **Modal obligatorio** (cuando vence el trial)

---

### 4.3. Integración con Wompi

#### Configuración Inicial

```python
# config/settings.py

# Wompi Configuration
WOMPI_PUBLIC_KEY = env('WOMPI_PUBLIC_KEY', default='')
WOMPI_PRIVATE_KEY = env('WOMPI_PRIVATE_KEY', default='')
WOMPI_EVENTS_SECRET = env('WOMPI_EVENTS_SECRET', default='')  # Para verificar webhooks
WOMPI_API_URL = 'https://production.wompi.co/v1'
WOMPI_TEST_MODE = env.bool('WOMPI_TEST_MODE', default=False)

# Planes de suscripción
PLANES_SUSCRIPCION = {
    'mensual': {
        'nombre': 'Plan Premium Mensual',
        'precio': 29900,  # COP $29.900 - "Por menos de mil pesos diarios organizarás tu negocio"
        'duracion_dias': 30,
        'descripcion': 'Acceso completo a todas las funciones'
    }
    # NO hay plan anual, solo mensual
}
```

#### Servicio de Wompi

```python
# apps/suscripciones/services/wompi_service.py

import requests
import hashlib
from django.conf import settings
from typing import Dict, Optional

class WompiService:
    """Servicio para integración con Wompi"""

    def __init__(self):
        self.api_url = settings.WOMPI_API_URL
        self.public_key = settings.WOMPI_PUBLIC_KEY
        self.private_key = settings.WOMPI_PRIVATE_KEY
        self.events_secret = settings.WOMPI_EVENTS_SECRET

    def crear_fuente_pago(self, tipo: str, datos: Dict) -> Dict:
        """
        Crear una fuente de pago (tokenización)
        tipo: 'CARD', 'NEQUI'
        """
        url = f"{self.api_url}/payment_sources"

        payload = {
            "type": tipo,
            "acceptance_token": datos.get('acceptance_token'),
            "customer_email": datos.get('email'),
            **datos
        }

        headers = {
            "Authorization": f"Bearer {self.public_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        return response.json()

    def crear_transaccion_recurrente(
        self,
        payment_source_id: str,
        monto: int,
        referencia: str,
        customer_email: str,
        descripcion: str = "Suscripción FacilAdmin"
    ) -> Dict:
        """
        Crear transacción recurrente usando token de pago
        monto: en centavos (ej: 49900 para $499.00 COP)
        """
        url = f"{self.api_url}/transactions"

        # Generar integridad
        integrity = self.generar_integridad(referencia, monto, 'COP')

        payload = {
            "amount_in_cents": monto,
            "currency": "COP",
            "customer_email": customer_email,
            "payment_method": {
                "type": "CARD",  # o NEQUI
                "token": payment_source_id,
                "installments": 1
            },
            "reference": referencia,
            "payment_source_id": payment_source_id,
            "redirect_url": f"{settings.SITE_URL}/suscripciones/confirmacion/",
            "signature:integrity": integrity
        }

        headers = {
            "Authorization": f"Bearer {self.private_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        return response.json()

    def consultar_transaccion(self, transaccion_id: str) -> Dict:
        """Consultar estado de una transacción"""
        url = f"{self.api_url}/transactions/{transaccion_id}"

        headers = {
            "Authorization": f"Bearer {self.public_key}"
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        return response.json()

    def generar_integridad(self, referencia: str, monto: int, moneda: str) -> str:
        """Generar hash de integridad para transacción"""
        cadena = f"{referencia}{monto}{moneda}{self.events_secret}"
        return hashlib.sha256(cadena.encode()).hexdigest()

    def verificar_webhook(self, payload: Dict, signature: str) -> bool:
        """Verificar firma de webhook"""
        # Implementar según documentación de Wompi
        # Típicamente involucra verificar HMAC signature
        import hmac

        # Convertir payload a string
        payload_str = json.dumps(payload, separators=(',', ':'))

        # Calcular HMAC
        expected_signature = hmac.new(
            self.events_secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature)
```

---

### 4.4. Vistas Principales

```python
# apps/suscripciones/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.urls import reverse
from datetime import timedelta
import secrets

from .models import RegistroNegocio, Suscripcion, PlanSuscripcion, PagoSuscripcion
from .services.wompi_service import WompiService

def registro_negocio(request):
    """Paso 1: Formulario de registro inicial SIMPLIFICADO + Cupón opcional"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        telefono = request.POST.get('telefono')
        email = request.POST.get('email')
        codigo_cupon = request.POST.get('codigo_cupon', '').strip().upper()

        # Validar que no exista
        if RegistroNegocio.objects.filter(email=email).exists():
            messages.error(request, 'Este email ya está registrado')
            return redirect('registro_negocio')

        # Validar cupón si se proporcionó
        cupon_obj = None
        if codigo_cupon:
            try:
                cupon_obj = Cupon.objects.get(codigo=codigo_cupon, activo=True)
                if not cupon_obj.esta_valido:
                    messages.warning(request, f'El cupón "{codigo_cupon}" no es válido o ha expirado')
                    cupon_obj = None
                elif not cupon_obj.solo_registro:
                    messages.warning(request, f'El cupón "{codigo_cupon}" solo puede usarse en el checkout')
                    cupon_obj = None
                else:
                    messages.success(request, f'¡Cupón "{codigo_cupon}" aplicado! 🎉')
            except Cupon.DoesNotExist:
                messages.warning(request, f'El cupón "{codigo_cupon}" no existe')

        # Generar token de validación
        token = secrets.token_urlsafe(32)
        fecha_expira = timezone.now() + timedelta(hours=24)

        # Crear registro
        registro = RegistroNegocio.objects.create(
            nombre=nombre,
            apellido=apellido,
            email=email,
            telefono=telefono,
            codigo_cupon=codigo_cupon if cupon_obj else None,
            cupon_aplicado=cupon_obj,
            token_validacion=token,
            fecha_token_expira=fecha_expira
        )

        # Enviar email de validación
        link_validacion = request.build_absolute_uri(
            reverse('validar_email', kwargs={'token': token})
        )

        send_mail(
            subject='✨ Activa tu cuenta gratis de 120 días - FacilAdmin',
            message=f'''
            Hola {nombre},

            ¡Bienvenido a FacilAdmin! 🎉

            Estás a un paso de acceder a tu cuenta GRATIS por 120 días con todas las funciones incluidas.

            👉 Activa tu cuenta aquí:
            {link_validacion}

            Este enlace expira en 24 horas.

            ¿Qué obtienes?
            ✅ 120 días completamente gratis
            ✅ Acceso completo a todas las funciones
            ✅ Citas ilimitadas
            ✅ Notificaciones push
            ✅ Soporte técnico

            ¡Nos vemos dentro!
            Equipo FacilAdmin
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        messages.success(request, '¡Casi listo! Te enviamos un email para activar tu cuenta gratis.')
        return redirect('registro_pendiente')

    return render(request, 'suscripciones/registro.html')


def validar_email(request, token):
    """Paso 2 y 3: Validar email y completar registro en un solo paso"""
    registro = get_object_or_404(RegistroNegocio, token_validacion=token)

    if not registro.token_valido:
        messages.error(request, 'El enlace ha expirado. Solicita uno nuevo.')
        return redirect('registro_negocio')

    if registro.estado == 'completado':
        messages.info(request, 'Esta cuenta ya fue activada. Puedes iniciar sesión.')
        return redirect('login')

    # Si es GET, mostrar formulario para completar
    if request.method == 'POST':
        nombre_negocio = request.POST.get('nombre_negocio')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        # Validaciones
        if password != password_confirm:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'suscripciones/activar_cuenta.html', {'registro': registro})

        if len(password) < 8:
            messages.error(request, 'La contraseña debe tener al menos 8 caracteres')
            return render(request, 'suscripciones/activar_cuenta.html', {'registro': registro})

        # Crear todo automáticamente
        from apps.negocios.models import Negocio
        from django.contrib.auth.models import User
        from django.contrib.auth import login

        # Crear usuario admin
        user = User.objects.create_user(
            username=registro.email,  # Usamos email como username
            email=registro.email,
            password=password,
            first_name=registro.nombre,
            last_name=registro.apellido
        )

        # Crear negocio
        negocio = Negocio.objects.create(
            nombre=nombre_negocio,
            telefono=registro.telefono,
            email=registro.email,
            dueno=user,
            esta_activo=True
        )

        # Crear suscripción trial automática
        plan_trial = PlanSuscripcion.objects.get(tipo='trial')

        # Calcular duración del trial (con cupón si aplica)
        dias_trial = 120  # Trial estándar
        meses_extra = 0

        if registro.cupon_aplicado and registro.cupon_aplicado.solo_registro:
            # Aplicar cupón que extiende trial
            meses_extra = registro.cupon_aplicado.meses_gratis
            dias_trial += (meses_extra * 30)

            # Registrar uso del cupón
            UsoCupon.objects.create(
                cupon=registro.cupon_aplicado,
                negocio=negocio,
                meses_extendidos=meses_extra
            )

            # Incrementar contador
            registro.cupon_aplicado.usos_actuales += 1
            registro.cupon_aplicado.save()

        suscripcion = Suscripcion.objects.create(
            negocio=negocio,
            plan=plan_trial,
            estado='trial',
            fecha_inicio=timezone.now(),
            fecha_fin=timezone.now() + timedelta(days=dias_trial),
            auto_renovacion=False
        )

        # Actualizar registro
        registro.estado = 'completado'
        registro.email_validado_en = timezone.now()
        registro.negocio_creado = negocio
        registro.save()

        # Login automático
        login(request, user)

        # Enviar email de bienvenida
        mensaje_cupon = ""
        if meses_extra > 0:
            mensaje_cupon = f"\n🎁 ¡Cupón aplicado! Obtuviste {meses_extra} mes(es) extra gratis.\n"

        send_mail(
            subject=f'🎉 ¡Bienvenido a FacilAdmin, {registro.nombre}!',
            message=f'''
            Hola {registro.nombre},

            ¡Tu cuenta de FacilAdmin está lista y activa!

            🏢 Negocio: {nombre_negocio}
            📧 Email: {registro.email}
            ⏰ Plan gratuito válido hasta: {suscripcion.fecha_fin.strftime('%d/%m/%Y')}
            {mensaje_cupon}
            Accede a tu panel aquí: {settings.SITE_URL}/admin/dashboard/

            Durante los próximos {dias_trial} días tendrás acceso COMPLETO a:
            ✅ Gestión ilimitada de citas
            ✅ Clientes y servicios ilimitados
            ✅ Notificaciones push
            ✅ Página web personalizada
            ✅ Código QR para reservas
            ✅ Soporte técnico

            💡 Tip: Completa el wizard de configuración para personalizar tu negocio.

            ¿Preguntas? Responde este email o escríbenos a WhatsApp.

            ¡Éxitos!
            Equipo FacilAdmin
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[registro.email],
            fail_silently=False,
        )

        messages.success(request, f'¡Bienvenido {registro.nombre}! Tu cuenta está activa por 120 días.')

        # Redirigir a dashboard con onboarding
        return redirect('admin_dashboard_onboarding')  # Vista con wizard de onboarding

    # GET: Mostrar formulario
    return render(request, 'suscripciones/activar_cuenta.html', {'registro': registro})


def suscribirse(request):
    """Vista para actualizar de trial a premium"""
    negocio = request.user.negocio  # Asumiendo relación OneToOne
    suscripcion = negocio.suscripcion

    if request.method == 'POST':
        plan_tipo = request.POST.get('plan')  # 'mensual' o 'anual'

        plan = PlanSuscripcion.objects.get(tipo=plan_tipo)

        # Redirigir a pasarela de Wompi
        wompi = WompiService()

        # Aquí se implementaría el flujo completo de Wompi
        # Por ahora, esto es un esqueleto

        return redirect('wompi_checkout', plan_id=plan.id)

    planes = PlanSuscripcion.objects.filter(tipo__in=['mensual', 'anual'], activo=True)

    context = {
        'suscripcion': suscripcion,
        'planes': planes,
        'dias_restantes': suscripcion.dias_restantes
    }

    return render(request, 'suscripciones/planes.html', context)
```

---

### 4.5. Webhooks de Wompi

```python
# apps/suscripciones/webhooks.py

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import logging

from .models import PagoSuscripcion, Suscripcion
from .services.wompi_service import WompiService

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def wompi_webhook(request):
    """
    Recibir notificaciones de Wompi sobre transacciones

    Eventos importantes:
    - transaction.updated: Cuando cambia el estado de una transacción
    """
    try:
        # Obtener payload y signature
        payload = json.loads(request.body)
        signature = request.headers.get('X-Signature', '')

        # Verificar firma
        wompi = WompiService()
        if not wompi.verificar_webhook(payload, signature):
            logger.warning(f"Webhook signature inválida: {payload}")
            return HttpResponse(status=403)

        # Procesar evento
        evento = payload.get('event')
        data = payload.get('data', {})

        if evento == 'transaction.updated':
            procesar_transaccion_actualizada(data)

        return JsonResponse({'status': 'ok'})

    except Exception as e:
        logger.error(f"Error procesando webhook: {str(e)}", exc_info=True)
        return HttpResponse(status=500)


def procesar_transaccion_actualizada(data: dict):
    """Procesar actualización de transacción"""
    transaccion_id = data.get('transaction', {}).get('id')
    status = data.get('transaction', {}).get('status')
    referencia = data.get('transaction', {}).get('reference')

    try:
        pago = PagoSuscripcion.objects.get(transaccion_id=transaccion_id)
    except PagoSuscripcion.DoesNotExist:
        logger.warning(f"Pago no encontrado para transacción {transaccion_id}")
        return

    # Actualizar estado del pago
    if status == 'APPROVED':
        pago.estado = 'aprobado'
        pago.save()

        # Activar/renovar suscripción
        activar_suscripcion(pago.suscripcion)

    elif status == 'DECLINED':
        pago.estado = 'rechazado'
        pago.save()

        # Enviar email notificando fallo
        notificar_pago_rechazado(pago)

    elif status == 'VOIDED':
        pago.estado = 'reembolsado'
        pago.save()

        # Suspender suscripción
        suspender_suscripcion(pago.suscripcion)


def activar_suscripcion(suscripcion: Suscripcion):
    """Activar o renovar suscripción después de pago exitoso"""
    from datetime import timedelta
    from django.utils import timezone

    if suscripcion.estado == 'trial':
        # Convertir de trial a activa
        suscripcion.estado = 'activa'

    # Extender fecha de fin
    if suscripcion.fecha_fin < timezone.now():
        # Suscripción vencida, renovar desde ahora
        suscripcion.fecha_fin = timezone.now() + timedelta(days=suscripcion.plan.duracion_dias)
    else:
        # Suscripción activa, extender desde fecha actual de fin
        suscripcion.fecha_fin += timedelta(days=suscripcion.plan.duracion_dias)

    suscripcion.save()

    # Enviar email de confirmación
    notificar_suscripcion_activa(suscripcion)
```

---

## 5. CRONOGRAMA DE IMPLEMENTACIÓN

### Sprint 1 (Semana 1-2): Fundamentos
- [ ] Crear modelos de BD
- [ ] Migrar modelos
- [ ] Crear fixtures con planes iniciales
- [ ] Sistema de registro con validación email
- [ ] Tests unitarios de modelos

### Sprint 2 (Semana 3-4): Trial Gratuito
- [ ] Completar flujo de registro
- [ ] Crear suscripción trial automática
- [ ] Dashboard de suscripción (ver días restantes)
- [ ] Sistema de notificaciones de expiración
- [ ] Middleware para verificar suscripción activa

### Sprint 3 (Semana 5-6): Integración Wompi
- [ ] Configurar cuenta Wompi (modo sandbox)
- [ ] Implementar WompiService
- [ ] Vista de selección de planes
- [ ] Checkout con Wompi
- [ ] Webhooks de Wompi
- [ ] Tests de integración

### Sprint 4 (Semana 7-8): Gestión y Pulido
- [ ] Panel admin de suscripciones
- [ ] Cancelación de suscripciones
- [ ] Historial de pagos
- [ ] Facturación automática (PDF)
- [ ] Emails transaccionales
- [ ] Documentación

### Sprint 5 (Semana 9): Testing y Deploy
- [ ] Tests end-to-end
- [ ] Seguridad (rate limiting, validaciones)
- [ ] Deploy a producción
- [ ] Monitoreo y alertas
- [ ] Go-live con Wompi producción

---

## 6. CONSIDERACIONES ADICIONALES

### 6.1. Seguridad
- ✅ HTTPS obligatorio para todas las transacciones
- ✅ Nunca almacenar tarjetas completas (solo tokens de Wompi)
- ✅ Validar webhooks con signature
- ✅ Rate limiting en endpoints de pago
- ✅ Logs de auditoría para todas las transacciones

### 6.2. UX/UI
- Flujo de pago en máximo 3 clics
- Mostrar claramente días restantes de trial
- Notificaciones no intrusivas (banners discretos)
- Posibilidad de cambiar de plan fácilmente
- Portal de auto-gestión (ver facturas, cancelar, etc.)

### 6.3. Legal
- Términos y condiciones claros
- Política de privacidad (GDPR-friendly)
- Política de reembolsos
- Aviso de renovación automática
- Facturación electrónica (DIAN si aplica en Colombia)

### 6.4. Soporte
- Email de soporte: soporte@faciladmin.app
- WhatsApp para clientes premium
- Base de conocimiento (FAQ)
- Onboarding para nuevos usuarios

---

## 7. MÉTRICAS A MONITOREAR

### KPIs de Negocio
- Tasa de conversión trial → premium
- Churn rate (cancelaciones)
- MRR (Monthly Recurring Revenue)
- LTV (Lifetime Value)
- Tiempo promedio en trial antes de convertir

### KPIs Técnicos
- Tasa de éxito de pagos
- Tiempo de respuesta de Wompi
- Uptime de webhooks
- Errores en transacciones

---

## 8. PRESUPUESTO ESTIMADO

### Costos de Pasarela (Wompi) - ACTUALIZADO

```
Asumiendo 100 suscripciones mensuales de $29.900 COP:
- Ingreso mensual: $2.990.000 COP

Escenario 1: Mix 50% PSE / 50% Tarjetas+Nequi
- PSE (1.49%): $22.301 COP (50 clientes)
- Tarjetas+Nequi (2.5%): $37.375 COP (50 clientes)
- Comisión total: $59.676 COP/mes
- Ingreso neto: $2.930.324 COP

Escenario 2: Todos por PSE (ideal)
- PSE (1.49%): $44.551 COP
- Ingreso neto: $2.945.449 COP
```

### Costos de Infraestructura
- Railway (DB + App): ~$20 USD/mes (~$90.000 COP)
- Emails transaccionales: Ya configurado (sin costo adicional)
- **Total: ~$90.000 COP/mes**

### Margen Estimado (100 clientes) - ACTUALIZADO
```
Ingreso mensual:      $2.990.000 COP
- Comisión Wompi:       -$59.676 COP (mix PSE/tarjetas)
- Infraestructura:      -$90.000 COP
────────────────────────────────────
= Margen neto:        $2.840.324 COP/mes

Por cliente:
- Ingreso por cliente: $29.900
- Costo por cliente:   $1.497 (comisión + infra)
- Margen por cliente:  $28.403 (95% de margen 🚀)

Punto de equilibrio: ~7 clientes pagos
```

---

## 9. ESTRATEGIAS DE CUPONES PARA FIDELIZACIÓN

### 9.1. Programa de Referidos (Recomendado)

```python
# Generar cupón único por usuario
def generar_cupon_referido(negocio):
    """
    Cada negocio obtiene un cupón único para compartir
    """
    codigo = f"REF-{negocio.id:05d}"  # Ej: REF-00001

    cupon, created = Cupon.objects.get_or_create(
        codigo=codigo,
        defaults={
            'tipo': 'mes_gratis',
            'meses_gratis': 1,
            'descripcion': f'Cupón de referido de {negocio.nombre}',
            'solo_nuevos_usuarios': True,
            'solo_registro': False,  # Se usa en checkout
            'activo': True
        }
    )

    return cupon
```

**Flujo:**
1. Usuario A (referidor) comparte su cupón `REF-00001`
2. Usuario B (referido) se registra y usa el cupón en checkout
3. Usuario B obtiene 1 mes gratis
4. Usuario A recibe notificación y también 1 mes gratis (bonus de referido)

**Incentivo:** Por cada 5 referidos, 1 mes gratis adicional

---

### 9.2. Cupones de Lanzamiento

```python
# Crear cupones limitados para lanzamiento
Cupon.objects.create(
    codigo='LANZAMIENTO100',
    tipo='descuento_porcentaje',
    porcentaje_descuento=50,  # 50% off
    descripcion='Descuento de lanzamiento - Primeros 100 usuarios',
    fecha_expiracion=timezone.now() + timedelta(days=30),
    usos_maximos=100,
    solo_nuevos_usuarios=True,
    solo_registro=False
)
```

**Copy de marketing:**
> "¡Únete a los primeros 100! Obtén 50% de descuento en tu primer mes con el código LANZAMIENTO100"

---

### 9.3. Recuperación de Churners (Win-back)

```python
# Comando para generar cupones de win-back
def generar_cupones_winback():
    """
    Genera cupones para usuarios que cancelaron hace 30+ días
    """
    fecha_limite = timezone.now() - timedelta(days=30)

    churners = Suscripcion.objects.filter(
        estado='cancelada',
        fecha_cancelacion__lte=fecha_limite
    )

    for suscripcion in churners:
        codigo = f"VUELVE-{suscripcion.negocio.id}"

        Cupon.objects.get_or_create(
            codigo=codigo,
            defaults={
                'tipo': 'mes_gratis',
                'meses_gratis': 1,
                'descripcion': 'Cupón de reactivación',
                'fecha_expiracion': timezone.now() + timedelta(days=60),
                'usos_maximos': 1,
                'solo_nuevos_usuarios': False,
                'activo': True
            }
        )

        # Enviar email personalizado
        enviar_email_winback(suscripcion.negocio, codigo)
```

**Email de win-back:**
> "¡Te extrañamos! Vuelve a FacilAdmin y obtén 1 mes gratis con el código VUELVE-XXXXX"

---

### 9.4. Fidelización por Antigüedad

```python
# Cupones automáticos por milestones
MILESTONES = {
    3: {'descuento': 10, 'mensaje': '¡3 meses con nosotros!'},
    6: {'descuento': 15, 'mensaje': '¡Medio año juntos!'},
    12: {'descuento': 20, 'mensaje': '¡1 año de éxito!'},
    24: {'descuento': 30, 'mensaje': '¡2 años increíbles!'}
}

def generar_cupones_aniversario():
    """
    Genera cupones de aniversario automáticamente
    """
    for meses, config in MILESTONES.items():
        fecha_inicio = timezone.now() - timedelta(days=meses*30+5)
        fecha_fin = timezone.now() - timedelta(days=meses*30-5)

        suscripciones = Suscripcion.objects.filter(
            estado='activa',
            fecha_inicio__gte=fecha_inicio,
            fecha_inicio__lte=fecha_fin
        )

        for sub in suscripciones:
            codigo = f"ANIVERSARIO{meses}-{sub.negocio.id}"

            Cupon.objects.create(
                codigo=codigo,
                tipo='descuento_porcentaje',
                porcentaje_descuento=config['descuento'],
                descripcion=f"Cupón de {meses} meses",
                fecha_expiracion=timezone.now() + timedelta(days=30),
                usos_maximos=1
            )

            # Enviar email de felicitación
            enviar_email_aniversario(sub.negocio, codigo, config['mensaje'])
```

---

### 9.5. Cupones Estacionales

```python
# Navidad
Cupon.objects.create(
    codigo='NAVIDAD2026',
    tipo='mes_gratis',
    meses_gratis=1,
    fecha_inicio=datetime(2026, 12, 1),
    fecha_expiracion=datetime(2026, 12, 31),
    descripcion='Promoción de Navidad'
)

# San Valentín (para spas/salones)
Cupon.objects.create(
    codigo='AMOR2026',
    tipo='descuento_porcentaje',
    porcentaje_descuento=25,
    fecha_inicio=datetime(2026, 2, 10),
    fecha_expiracion=datetime(2026, 2, 14),
    descripcion='Promoción San Valentín'
)

# Día de la madre
Cupon.objects.create(
    codigo='MAMA2026',
    tipo='mes_gratis',
    meses_gratis=1,
    fecha_inicio=datetime(2026, 5, 1),
    fecha_expiracion=datetime(2026, 5, 15),
    descripcion='Promoción Día de la Madre'
)
```

---

### 9.6. Cupones para Influencers/Partners

```python
# Crear cupones personalizados
def crear_cupon_colaborador(nombre_colaborador, usos=50):
    codigo = f"COLABORA-{nombre_colaborador.upper()}"

    return Cupon.objects.create(
        codigo=codigo,
        tipo='mes_gratis',
        meses_gratis=2,  # 2 meses gratis
        descripcion=f'Cupón de colaboración con {nombre_colaborador}',
        usos_maximos=usos,
        solo_nuevos_usuarios=True,
        activo=True
    )

# Uso:
crear_cupon_colaborador('INFLUENCER1', usos=100)
# Genera: COLABORA-INFLUENCER1
```

---

### 9.7. Panel de Analytics de Cupones

```python
# Vista para ver estadísticas de cupones
def estadisticas_cupones(request):
    """
    Dashboard de performance de cupones
    """
    cupones = Cupon.objects.annotate(
        total_usos=Count('usos'),
        conversion_rate=F('usos_actuales') * 100.0 / F('usos_maximos')
    ).order_by('-total_usos')

    # Métricas
    metricas = {
        'total_cupones_activos': Cupon.objects.filter(activo=True).count(),
        'total_usos': UsoCupon.objects.count(),
        'meses_regalados': UsoCupon.objects.aggregate(Sum('meses_extendidos'))['meses_extendidos__sum'] or 0,
        'descuentos_otorgados': UsoCupon.objects.aggregate(Sum('descuento_aplicado'))['descuento_aplicado__sum'] or 0,
        'cupon_mas_usado': cupones.first(),
        'tasa_conversion_promedio': cupones.aggregate(Avg('conversion_rate'))['conversion_rate__avg']
    }

    return render(request, 'suscripciones/analytics_cupones.html', {
        'cupones': cupones,
        'metricas': metricas
    })
```

**Métricas a monitorear:**
- Cupones más utilizados
- Tasa de conversión por cupón
- ROI de cupones (meses regalados vs clientes retenidos)
- Cupones por fuente (referidos, marketing, partners)

---

## 10. PRÓXIMOS PASOS INMEDIATOS

### ✅ CONFIRMACIONES RECIBIDAS

1. ✅ **Precio**: $29.900 COP/mes ("Por menos de mil pesos diarios organizarás tu negocio")
2. ✅ **Plan único**: Solo mensual (NO plan anual)
3. ✅ **Trial**: 120 días full access gratis
4. ✅ **Premium**: Mismas features que trial, solo pago para continuar
5. ✅ **Pasarela**: Wompi
6. ✅ **Métodos de pago**: Todos (PSE + Tarjetas + Nequi)
7. ✅ **Email**: Ya configurado
8. ✅ **Facturación**: Simple sin IVA por ahora
9. ✅ **Onboarding**: Ya existe, solo ajustar si necesario

### 🚀 PLAN DE IMPLEMENTACIÓN

#### Sprint 1 (Semana 1-2): Modelos y Registro
- [ ] Crear app `apps/suscripciones/`
- [ ] Crear modelos: `PlanSuscripcion`, `Suscripcion`, `PagoSuscripcion`, `RegistroNegocio`
- [ ] Crear modelos de cupones: `Cupon`, `UsoCupon`
- [ ] Migraciones
- [ ] Fixture con plan trial + plan mensual $29.900
- [ ] Vista de registro simplificado (4 campos + cupón opcional)
- [ ] Template de registro minimalista con campo de cupón colapsable
- [ ] Lógica de validación de cupones en registro
- [ ] Email de validación con token
- [ ] Vista de activación (2 campos: nombre negocio + password)
- [ ] Auto-creación de negocio + suscripción trial (con extensión si hay cupón)
- [ ] Login automático
- [ ] Admin de cupones en Django admin

#### Sprint 2 (Semana 3): Dashboard y Botón Premium
- [ ] Middleware para verificar suscripción activa
- [ ] Context processor para datos de suscripción
- [ ] Botón "Hacerse Premium" en navbar (dinámico según días)
- [ ] Banner de notificación (cuando faltan <30 días)
- [ ] Modal obligatorio (cuando vence trial)
- [ ] Vista de planes (mostrar solo $29.900/mes)
- [ ] Revisar/ajustar onboarding existente si necesario

#### Sprint 3 (Semana 4-5): Integración Wompi
- [ ] Crear cuenta Wompi sandbox
- [ ] Configurar credenciales en .env
- [ ] Servicio `WompiService` (tokenización, transacciones, webhooks)
- [ ] Vista de checkout con Wompi
- [ ] Página de selección de método de pago (PSE/Tarjetas/Nequi)
- [ ] Webhook para confirmar pagos
- [ ] Activación/renovación automática de suscripción
- [ ] Emails de confirmación

#### Sprint 4 (Semana 6-7): Gestión y Admin
- [ ] Panel admin para ver suscripciones
- [ ] Vista de historial de pagos
- [ ] Cancelación de suscripción
- [ ] Generación de facturas simples (PDF)
- [ ] Comando Django para notificar vencimientos (día 90, 110, 115, 119)
- [ ] Cron job / Celery para ejecutar notificaciones

#### Sprint 5 (Semana 8-9): Testing y Producción
- [ ] Tests unitarios de modelos
- [ ] Tests de integración con Wompi
- [ ] Tests E2E de flujo completo
- [ ] Migrar cuenta Wompi a producción
- [ ] Deploy a Railway
- [ ] Monitoreo de webhooks
- [ ] Documentación

---

## 📋 RESUMEN EJECUTIVO FINAL

### 💰 Modelo de Negocio
```
Trial:    GRATIS por 120 días (full access)
          + Opción de cupón (extiende trial o descuento en pago)
          ↓
Premium:  $29.900 COP/mes
          "Por menos de mil pesos diarios organizarás tu negocio"
```

### 🎁 Sistema de Cupones
```
✅ 3 tipos de cupones:
   - Mes gratis (extiende trial o primer mes gratis)
   - Descuento % (ej: 50% off)
   - Descuento fijo (ej: $10.000 off)

✅ Aplicación:
   - En registro: Extiende trial (120 → 150 días)
   - En checkout: Descuento o mes gratis en pago

✅ Estrategias:
   - Programa de referidos (REF-00001)
   - Cupones de lanzamiento (LANZAMIENTO100)
   - Recuperación de churners (VUELVE-XXXXX)
   - Fidelización por antigüedad (ANIVERSARIO12)
   - Promociones estacionales (NAVIDAD2026)
   - Colaboraciones (COLABORA-INFLUENCER1)
```

### 📊 Números Clave
- **Punto de equilibrio**: 7 clientes pagos
- **Margen por cliente**: 95% (~$28.400)
- **Con 100 clientes**: $2.840.000 COP/mes de margen neto

### 🎯 Estrategia
1. **Captación**: Registro ultra simple (2-3 minutos) + cupones opcionales
2. **Activación**: Onboarding guiado opcional
3. **Retención**: 120 días para crear hábito + cupones de fidelización
4. **Monetización**: Conversión natural al vencer trial
5. **Crecimiento**: Boca a boca + bajo precio ($999/día) + programa de referidos
6. **Recuperación**: Cupones de win-back para usuarios inactivos

---

## ❓ ¿LISTO PARA EMPEZAR?

Todo está planificado y confirmado. ¿Empezamos con el **Sprint 1** (crear modelos y registro)?

---

**Autor**: Claude
**Fecha**: 2026-08-29
**Versión**: 1.0
