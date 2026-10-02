"""
Montos en pesos colombianos: formato para mostrar y lectura de lo que se escribe
"""
import re
from decimal import Decimal


def pesos(valor):
    """20000 -> '$20.000' (sin decimales, separador de miles con punto)"""
    if valor is None or valor == '':
        return ''
    return '$' + f'{int(round(Decimal(valor))):,}'.replace(',', '.')


def parsear_monto(texto):
    """
    Lee un monto escrito por una persona: '50.000', '$ 50.000', '50000' -> Decimal(50000).
    Los pesos no usan centavos, así que se toman solo los dígitos.
    Retorna None si no hay un monto válido.
    """
    digitos = re.sub(r'\D', '', str(texto or ''))
    if not digitos:
        return None
    return Decimal(digitos)
