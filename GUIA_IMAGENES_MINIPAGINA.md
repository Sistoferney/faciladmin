# Guía de Imágenes para Mini-Página

Esta guía te ayudará a preparar las imágenes correctas para personalizar tu mini-página de negocio.

## 📸 Imágenes Requeridas

### 1. Logo del Negocio

**Campo**: `logo`

#### 📏 Medidas Recomendadas:
- **Tamaño ideal**: 800 x 400 px (horizontal) o 600 x 600 px (cuadrado)
- **Tamaño mínimo**: 400 x 200 px
- **Tamaño máximo**: 1200 x 600 px
- **Formato**: PNG con fondo transparente (recomendado) o JPG
- **Peso máximo**: 500 KB

#### 💡 Recomendaciones:
- ✅ Usa PNG con **fondo transparente** para mejor integración
- ✅ Puede ser **horizontal** (ideal para logos con nombre del negocio)
- ✅ Alta resolución para que se vea nítida en pantallas Retina
- ✅ Logos simples y legibles se ven mejor en móviles
- ❌ Evita logos muy detallados que no se lean en tamaños pequeños

#### 📱 Dónde se muestra:
- **Navbar** de la mini-página (120px altura x 350px ancho máximo)
- Favicon del navegador (192x192 px)
- Emails y notificaciones
- Confirmaciones de citas
- Icono de la PWA (app instalable)

#### 🎨 Tamaños de visualización:
| Dispositivo | Tamaño en navbar |
|-------------|------------------|
| Desktop/Tablet | 120px altura, máx 350px ancho |
| Móvil | 120px altura, máx 350px ancho |
| Favicon | 192x192 px (cuadrado) |

---

### 2. Imagen de Portada (Hero/Banner)

**Campo**: `imagen_portada`

#### 📏 Medidas Recomendadas (Responsive):
- **Tamaño ideal**: 1600 x 900 px (proporción 16:9) ⭐ **RECOMENDADO**
- **Alternativa**: 1200 x 800 px (proporción 3:2)
- **Tamaño mínimo**: 1200 x 675 px
- **Tamaño máximo**: 2400 x 1350 px
- **Formato**: JPG (preferido para fotos) o PNG
- **Peso máximo**: 500 KB (comprimido)

#### 💡 Recomendaciones:
- ✅ Usa **proporción 16:9** para mejor compatibilidad móvil/desktop
- ✅ Alta calidad, bien iluminada
- ✅ Muestra el ambiente del negocio (instalaciones, servicios)
- ✅ **SIN texto en la imagen** (solo aparece botón pequeño abajo)
- ✅ Comprime la imagen sin perder calidad (usa TinyPNG o Squoosh)
- ✅ Elementos importantes en el **centro** de la imagen
- ❌ Evita imágenes borrosas o pixeladas
- ❌ No uses fotos con marcas de agua

#### 📱 Visualización Responsive:
| Dispositivo | Altura | Comportamiento |
|-------------|--------|----------------|
| **Desktop** | 400px | Se recorta (`cover`) mostrando la parte central |
| **Tablet** | 400px | Se recorta (`cover`) mostrando la parte central |
| **Móvil** | 300px | Se muestra completa (`contain`) con fondo negro |

#### 🎨 Contenido sugerido:
- 🛋️ Interior del spa/salón (vista amplia)
- 💆 Persona recibiendo servicio (profesional)
- 🌿 Productos o ambiente relajante
- ✨ Instalaciones limpias y atractivas

#### 🖼️ Zona de Seguridad (IMPORTANTE):
```
┌─────────────────────────────────────────┐
│          Puede cortarse (Desktop)       │
├─────────────────────────────────────────┤
│                                         │
│        ┌───────────────────┐           │
│        │   ZONA SEGURA     │           │
│        │   (Centro 800px)  │           │
│        │                   │           │
│        │ Contenido clave   │           │
│        │ aquí se ve en     │           │
│        │ todos los         │           │
│        │ dispositivos      │           │
│        └───────────────────┘           │
│                                         │
├─────────────────────────────────────────┤
│          Puede cortarse (Desktop)       │
└─────────────────────────────────────────┘
```

**Regla de oro**: Mantén los elementos importantes (logos, personas, productos) en el **centro de la imagen** (zona ~800x600px) para asegurar visibilidad en todos los dispositivos.

---

## 🎨 Paleta de Colores

Además de las imágenes, puedes personalizar:

### Color Primario
**Campo**: `color_primario`
- **Formato**: Hexadecimal (ej: #007bff)
- **Uso**: Botones, enlaces, encabezados
- **Recomendación**: Color de tu marca/logo

### Color Secundario
**Campo**: `color_secundario`
- **Formato**: Hexadecimal (ej: #6c757d)
- **Uso**: Textos secundarios, bordes, fondos sutiles
- **Recomendación**: Complementario al primario

#### 🎨 Paletas sugeridas para Spas/Salones:

| Estilo | Primario | Secundario | Descripción |
|--------|----------|------------|-------------|
| Spa Zen | `#8fbc8f` | `#daa520` | Verde salvia + Dorado |
| Elegante | `#2c3e50` | `#e74c3c` | Azul oscuro + Coral |
| Moderno | `#00b894` | `#fdcb6e` | Verde agua + Amarillo |
| Clásico | `#6c5ce7` | `#a29bfe` | Morado + Lila |
| Femenino | `#fd79a8` | `#fdcb6e` | Rosa + Dorado claro |

---

## 🛠️ Herramientas Recomendadas

### Para Editar/Redimensionar:
- **Canva** (online, gratis) - https://canva.com
- **Photopea** (online, gratis) - https://photopea.com
- **GIMP** (desktop, gratis) - https://gimp.org
- **Photoshop** (desktop, pago)

### Para Comprimir Imágenes:
- **TinyPNG** - https://tinypng.com
- **ImageOptim** (Mac) - https://imageoptim.com
- **Squoosh** (online, Google) - https://squoosh.app

### Para Remover Fondo (Logo):
- **Remove.bg** - https://remove.bg
- **PhotoScissors** - https://photoscissors.com

### Para Obtener Colores:
- **Adobe Color** - https://color.adobe.com
- **Coolors** - https://coolors.co
- **ColorHunt** - https://colorhunt.co

---

## 📋 Checklist Antes de Subir

### Logo:
- [ ] Tamaño: 800x400 px (horizontal) o 600x600 px (cuadrado)
- [ ] Formato: PNG con fondo transparente
- [ ] Peso: Menor a 500 KB
- [ ] Se ve nítido al hacer zoom
- [ ] Legible en tamaño pequeño
- [ ] Texto legible si incluye nombre del negocio

### Imagen de Portada:
- [ ] Tamaño: 1600x900 px (proporción 16:9) ⭐
- [ ] Formato: JPG comprimido
- [ ] Peso: Menor a 500 KB
- [ ] Imagen comprimida (TinyPNG o Squoosh)
- [ ] Alta calidad, bien iluminada
- [ ] Elementos importantes en el centro (zona segura)
- [ ] Representa bien el negocio
- [ ] Sin texto ni marcas de agua
- [ ] Sin elementos críticos en los bordes

### Colores:
- [ ] Color primario definido (#RRGGBB)
- [ ] Color secundario definido (#RRGGBB)
- [ ] Colores tienen buen contraste
- [ ] Colores reflejan la marca

---

## 📂 Estructura de Archivos en el Servidor

Las imágenes se suben a:
```
media/
├── negocios/
│   ├── logos/
│   │   └── tu-logo.png
│   └── portadas/
│       └── tu-portada.jpg
```

---

## 🎯 Ejemplos de Referencias

### Spas:
- Imágenes de ambientes tranquilos
- Tonos verdes, azules, blancos
- Productos naturales, piedras, velas

### Peluquerías:
- Interior del salón, sillas
- Tonos modernos, contrastantes
- Herramientas profesionales

### Barberías:
- Ambiente masculino, vintage
- Tonos oscuros, madera
- Productos de barbería

---

## ❓ Preguntas Frecuentes

### ¿Puedo cambiar las imágenes después?
**Sí**, puedes actualizarlas en cualquier momento desde el panel de administración.

### ¿Qué pasa si no subo logo?
Se mostrará el nombre del negocio en texto.

### ¿Qué pasa si no subo imagen de portada?
Se usará un color de fondo sólido con el color primario.

### ¿Puedo usar imágenes de Google?
**No recomendado**. Usa imágenes propias o de bancos de imágenes libres:
- Unsplash - https://unsplash.com
- Pexels - https://pexels.com
- Pixabay - https://pixabay.com

### ¿El sistema redimensiona automáticamente?
Actualmente **no**. Debes subir las imágenes en el tamaño correcto.

---

## 📞 Soporte

Si tienes problemas subiendo imágenes:
1. Verifica el formato (PNG o JPG)
2. Verifica el tamaño (no más de 1MB)
3. Intenta comprimir la imagen
4. Contacta al administrador del sistema

---

**Última actualización**: 2026-06-17

---

## 📝 Changelog

### 2026-06-17
- ✅ Actualizado tamaño del logo: ahora 120px altura en navbar (antes 70px)
- ✅ Nuevo tamaño ideal de portada: 1600x900px (16:9) para mejor responsive
- ✅ Agregada zona de seguridad visual para portadas
- ✅ Actualizado comportamiento responsive: contain en móviles, cover en desktop
- ✅ Portada sin texto superpuesto, solo botón pequeño en parte inferior
