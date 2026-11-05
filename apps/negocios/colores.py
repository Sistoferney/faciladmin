"""
Colores de la marca del negocio

El dueño elige cualquier color, así que el texto se calcula para que siempre se
lea (contraste WCAG): sobre el color de marca y sobre el fondo blanco.
"""
import re

BLANCO = '#ffffff'
OSCURO = '#212529'
RESPALDO = '#6366f1'  # color guardado inválido o vacío

# Combinaciones listas en la configuración: (nombre, principal, secundario)
PALETAS = [
    ('Orquídea', '#d63384', '#6f42c1'),
    ('Coral', '#d9480f', '#d6336c'),
    ('Vino', '#7f1d3f', '#be185d'),
    ('Lavanda', '#7c3aed', '#a855f7'),
    ('Océano', '#1e3a8a', '#2563eb'),
    ('Esmeralda', '#0f766e', '#059669'),
    ('Canela', '#78503c', '#a9714b'),
    ('Negro y dorado', '#212529', '#8a6d1f'),
]

CONTRASTE_TEXTO_GRANDE = 3
CONTRASTE_TEXTO = 4.5


def a_rgb(color):
    if not re.fullmatch(r'#[0-9a-fA-F]{6}', color or ''):
        color = RESPALDO
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def _luminancia(color):
    canales = []
    for canal in a_rgb(color):
        c = canal / 255
        canales.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * canales[0] + 0.7152 * canales[1] + 0.0722 * canales[2]


def contraste(color_a, color_b):
    claro, oscuro = sorted((_luminancia(color_a), _luminancia(color_b)), reverse=True)
    return (claro + 0.05) / (oscuro + 0.05)


def texto_legible(*fondos):
    """
    Blanco mientras se lea (es lo que ya usan los negocios); si no, el que mejor
    se lea en todos los fondos. Un degradado pasa por varios: se mira cada extremo.
    """
    def peor_contraste(texto):
        return min(contraste(texto, fondo) for fondo in fondos)

    if peor_contraste(BLANCO) >= CONTRASTE_TEXTO_GRANDE:
        return BLANCO
    return max((BLANCO, OSCURO), key=peor_contraste)


def legible_sobre_blanco(color):
    """El mismo color, oscurecido lo necesario para usarlo como texto sobre blanco"""
    rgb = a_rgb(color)
    actual = '#%02x%02x%02x' % rgb
    while contraste(actual, BLANCO) < CONTRASTE_TEXTO:
        rgb = tuple(int(canal * 0.92) for canal in rgb)
        actual = '#%02x%02x%02x' % rgb
    return actual
