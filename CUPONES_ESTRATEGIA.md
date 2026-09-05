# Sistema de Cupones - FacilAdmin

## Resumen Rápido

Sistema flexible de cupones para fidelización, marketing y crecimiento de usuarios.

### 🎯 Objetivo
Implementar cupones de descuento y meses gratis como estrategia de:
- Adquisición de usuarios (cupones de lanzamiento)
- Fidelización (cupones de aniversario)
- Referidos (programa viral)
- Recuperación de churners (win-back)
- Colaboraciones (influencers/partners)

---

## 💡 Tipos de Cupones

### 1. Mes Gratis
```python
Cupon.objects.create(
    codigo='PROMO2026',
    tipo='mes_gratis',
    meses_gratis=1,
    descripcion='Promoción de lanzamiento'
)
```
**Aplicación:**
- En registro: Extiende trial (120 → 150 días)
- En checkout: Primer mes gratis

### 2. Descuento Porcentaje
```python
Cupon.objects.create(
    codigo='DESCUENTO50',
    tipo='descuento_porcentaje',
    porcentaje_descuento=50,
    descripcion='50% de descuento'
)
```
**Aplicación:** $29.900 → $14.950

### 3. Descuento Fijo
```python
Cupon.objects.create(
    codigo='10MIL',
    tipo='descuento_fijo',
    monto_descuento=10000,
    descripcion='$10.000 de descuento'
)
```
**Aplicación:** $29.900 → $19.900

---

## 📍 Dónde se Usan

### Opción A: Durante Registro
- Campo opcional: "¿Tienes un cupón?"
- Solo cupones con `solo_registro=True`
- Efecto: Extiende el trial
- Ejemplo: Trial 120 días + cupón 1 mes = 150 días gratis

### Opción B: Durante Checkout
- Campo: "Código de cupón"
- Cualquier tipo de cupón
- Efecto: Descuento o mes gratis en pago
- Ejemplo: Primer mes gratis, luego $29.900/mes

---

## 🚀 Estrategias Recomendadas

### 1. Programa de Referidos ⭐

**Cómo funciona:**
1. Cada usuario obtiene un cupón único: `REF-00001`
2. Comparte con amigos
3. Amigo se registra con cupón → 1 mes gratis
4. Usuario original también recibe 1 mes gratis

**Código:**
```python
def generar_cupon_referido(negocio):
    codigo = f"REF-{negocio.id:05d}"

    return Cupon.objects.get_or_create(
        codigo=codigo,
        defaults={
            'tipo': 'mes_gratis',
            'meses_gratis': 1,
            'solo_nuevos_usuarios': True,
        }
    )
```

**Incentivo adicional:**
- 1 referido = 1 mes gratis para ambos
- 5 referidos = 1 mes extra bonus
- 10 referidos = 2 meses extra bonus

---

### 2. Cupones de Lanzamiento

**Para primeros usuarios:**
```python
Cupon.objects.create(
    codigo='LANZAMIENTO100',
    tipo='descuento_porcentaje',
    porcentaje_descuento=50,
    usos_maximos=100,
    fecha_expiracion='2026-12-31'
)
```

**Copy de marketing:**
> "¡Únete a los primeros 100 usuarios y obtén 50% de descuento en tu primer mes!"

---

### 3. Recuperación de Churners (Win-back)

**Para usuarios que cancelaron:**
```python
# Comando automático
def generar_cupones_winback():
    churners = Suscripcion.objects.filter(
        estado='cancelada',
        fecha_cancelacion__lte=timezone.now() - timedelta(days=30)
    )

    for suscripcion in churners:
        codigo = f"VUELVE-{suscripcion.negocio.id}"

        Cupon.objects.create(
            codigo=codigo,
            tipo='mes_gratis',
            meses_gratis=1,
            usos_maximos=1,
            fecha_expiracion=timezone.now() + timedelta(days=60)
        )

        enviar_email_winback(suscripcion.negocio, codigo)
```

**Email:**
> "¡Te extrañamos! Vuelve con 1 mes gratis usando el código VUELVE-XXXXX"

---

### 4. Cupones de Fidelización

**Por antigüedad:**
```python
MILESTONES = {
    3: 10,   # 10% descuento a los 3 meses
    6: 15,   # 15% descuento a los 6 meses
    12: 20,  # 20% descuento al año
    24: 30   # 30% descuento a los 2 años
}

# Se generan automáticamente
def generar_cupones_aniversario():
    for meses, descuento in MILESTONES.items():
        # Encontrar usuarios que cumplan X meses
        suscripciones = obtener_suscripciones_aniversario(meses)

        for sub in suscripciones:
            codigo = f"ANIVERSARIO{meses}-{sub.negocio.id}"

            Cupon.objects.create(
                codigo=codigo,
                tipo='descuento_porcentaje',
                porcentaje_descuento=descuento,
                usos_maximos=1
            )

            enviar_email_felicitacion(sub.negocio, codigo)
```

---

### 5. Cupones Estacionales

**Navidad:**
```python
Cupon.objects.create(
    codigo='NAVIDAD2026',
    tipo='mes_gratis',
    meses_gratis=1,
    fecha_inicio='2026-12-01',
    fecha_expiracion='2026-12-31'
)
```

**San Valentín:**
```python
Cupon.objects.create(
    codigo='AMOR2026',
    tipo='descuento_porcentaje',
    porcentaje_descuento=25,
    fecha_inicio='2026-02-10',
    fecha_expiracion='2026-02-14'
)
```

**Día de la Madre:**
```python
Cupon.objects.create(
    codigo='MAMA2026',
    tipo='mes_gratis',
    meses_gratis=1,
    fecha_inicio='2026-05-01',
    fecha_expiracion='2026-05-15'
)
```

---

### 6. Cupones para Influencers/Partners

**Cupones personalizados:**
```python
def crear_cupon_colaborador(nombre, usos=50):
    codigo = f"COLABORA-{nombre.upper()}"

    return Cupon.objects.create(
        codigo=codigo,
        tipo='mes_gratis',
        meses_gratis=2,  # 2 meses gratis
        usos_maximos=usos,
        descripcion=f'Cupón de {nombre}'
    )

# Ejemplos:
crear_cupon_colaborador('INFLUENCER1', usos=100)  # COLABORA-INFLUENCER1
crear_cupon_colaborador('PODCAST', usos=200)       # COLABORA-PODCAST
crear_cupon_colaborador('CANAL', usos=500)         # COLABORA-CANAL
```

**Tracking:**
- Cada colaborador tiene código único
- Métricas de conversión por código
- Comisión/incentivo por referidos

---

## 📊 Métricas a Monitorear

### Dashboard de Cupones

**KPIs principales:**
- Total cupones activos
- Total usos de cupones
- Tasa de conversión por cupón
- ROI: Meses regalados vs retención
- Cupones más utilizados
- Fuente de cupones (referidos, marketing, partners)

**Vista de admin:**
```python
def estadisticas_cupones(request):
    cupones = Cupon.objects.annotate(
        total_usos=Count('usos'),
        conversion_rate=F('usos_actuales') * 100.0 / F('usos_maximos')
    )

    metricas = {
        'cupones_activos': Cupon.objects.filter(activo=True).count(),
        'total_usos': UsoCupon.objects.count(),
        'meses_regalados': UsoCupon.objects.aggregate(Sum('meses_extendidos')),
        'descuentos_otorgados': UsoCupon.objects.aggregate(Sum('descuento_aplicado')),
        'cupon_mas_usado': cupones.first(),
        'tasa_conversion': cupones.aggregate(Avg('conversion_rate'))
    }

    return render(request, 'analytics_cupones.html', metricas)
```

---

## 🎨 UI/UX de Cupones

### En Registro
```html
<form>
  <input name="nombre" placeholder="Nombre" required>
  <input name="apellido" placeholder="Apellido" required>
  <input name="telefono" placeholder="Teléfono" required>
  <input name="email" type="email" placeholder="Email" required>

  <!-- Campo de cupón COLAPSABLE -->
  <div class="cupon-toggle">
    <a href="#" onclick="toggleCupon()">¿Tienes un cupón? 🎁</a>
  </div>

  <div id="campo-cupon" style="display:none;">
    <input name="codigo_cupon"
           placeholder="Ingresa tu código"
           style="text-transform: uppercase;">
    <small>Ej: PROMO2026, REF-00001</small>
  </div>

  <button>Crear Cuenta Gratis</button>
</form>
```

### En Checkout
```html
<div class="resumen-pago">
  <h3>Resumen</h3>
  <p>Plan Premium Mensual: $29.900</p>

  <div class="aplicar-cupon">
    <input name="codigo_cupon" placeholder="Código de cupón">
    <button type="button" onclick="aplicarCupon()">Aplicar</button>
  </div>

  <div id="descuento-aplicado" style="display:none;">
    <p class="text-success">✅ Cupón aplicado</p>
    <p>Descuento: -$14.950</p>
    <hr>
    <p class="total">Total a pagar: $14.950</p>
  </div>
</div>
```

### Notificación de Cupón Aplicado
```html
<!-- Al aplicar cupón exitosamente -->
<div class="alert alert-success">
  🎉 ¡Cupón "PROMO2026" aplicado exitosamente!
  <br>
  Obtuviste: 1 mes gratis adicional
</div>
```

---

## 🔧 Comandos Django para Automatización

### Crear comando de cupones
```python
# apps/suscripciones/management/commands/generar_cupones.py

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Genera cupones automáticos'

    def add_arguments(self, parser):
        parser.add_argument('tipo', type=str, help='Tipo de cupones: referidos, winback, aniversario')

    def handle(self, *args, **options):
        tipo = options['tipo']

        if tipo == 'referidos':
            generar_cupones_referidos()
        elif tipo == 'winback':
            generar_cupones_winback()
        elif tipo == 'aniversario':
            generar_cupones_aniversario()

        self.stdout.write(self.style.SUCCESS(f'Cupones {tipo} generados'))
```

**Uso:**
```bash
python manage.py generar_cupones referidos
python manage.py generar_cupones winback
python manage.py generar_cupones aniversario
```

### Cron Jobs
```python
# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    'generar-cupones-aniversario': {
        'task': 'apps.suscripciones.tasks.generar_cupones_aniversario',
        'schedule': crontab(hour=10, minute=0),  # Diario a las 10 AM
    },
    'generar-cupones-winback': {
        'task': 'apps.suscripciones.tasks.generar_cupones_winback',
        'schedule': crontab(day_of_week=1, hour=9, minute=0),  # Lunes a las 9 AM
    }
}
```

---

## 📈 ROI de Cupones

### Cálculo de ROI

**Ejemplo 1: Cupón de Referidos**
- Cupón: REF-00001 (1 mes gratis)
- Costo: $29.900 (1 mes regalado)
- Beneficio: 2 usuarios nuevos (referidor + referido)
- LTV promedio: $359.000 (12 meses × $29.900)
- ROI: $718.000 / $29.900 = **2400% ROI**

**Ejemplo 2: Cupón de Lanzamiento**
- Cupón: LANZAMIENTO100 (50% descuento 1er mes)
- Costo: $14.950 por usuario × 100 = $1.495.000
- Beneficio: 100 usuarios nuevos
- Si 30% se quedan 6+ meses: 30 × 6 × $29.900 = $5.382.000
- ROI: $5.382.000 / $1.495.000 = **360% ROI**

**Ejemplo 3: Cupón Win-back**
- Cupón: VUELVE-XXXXX (1 mes gratis)
- Costo: $29.900 por usuario recuperado
- Tasa de reactivación: 15% (de 100 churners, 15 vuelven)
- Costo total: 15 × $29.900 = $448.500
- Beneficio: 15 × 12 × $29.900 = $5.382.000
- ROI: $5.382.000 / $448.500 = **1200% ROI**

---

## ✅ Checklist de Implementación

### Sprint 1
- [ ] Crear modelo `Cupon`
- [ ] Crear modelo `UsoCupon`
- [ ] Migraciones
- [ ] Admin de cupones

### Sprint 2
- [ ] Campo de cupón en registro (colapsable)
- [ ] Validación de cupón en registro
- [ ] Aplicación de cupón (extender trial)

### Sprint 3
- [ ] Campo de cupón en checkout
- [ ] Validación de cupón en checkout
- [ ] Aplicación de cupón (descuento)
- [ ] Webhooks de Wompi con cupones

### Sprint 4
- [ ] Comando generar_cupones (referidos, winback, aniversario)
- [ ] Emails de cupones
- [ ] Panel de analytics de cupones

### Sprint 5
- [ ] Tests de cupones
- [ ] Documentación
- [ ] Cron jobs (Celery Beat)

---

## 🎯 Quick Wins

**Implementar primero (orden de prioridad):**

1. **Cupones de registro** (más fácil, gran impacto)
   - Campo opcional en registro
   - Extiende trial automáticamente

2. **Programa de referidos** (efecto viral)
   - Cupón único por usuario
   - 1 mes gratis para ambos

3. **Cupón de lanzamiento** (urgente, marketing)
   - LANZAMIENTO100
   - 50% off primeros 100 usuarios

4. **Win-back automático** (recuperar ingresos)
   - Comando semanal
   - Email personalizado

5. **Analytics de cupones** (medir ROI)
   - Dashboard simple
   - Métricas clave

---

**Autor**: Claude
**Fecha**: 2026-08-29
**Versión**: 1.0
