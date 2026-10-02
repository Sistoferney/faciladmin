"""
Identificación de usuarios por teléfono

El teléfono es el identificador único de los usuarios. Un mismo número
puede escribirse de muchas formas (3001234567, 300 123 4567, +57 300 123 4567,
573001234567...), así que se normaliza a formato E.164 (+573001234567):
- Al registrar, se guarda normalizado.
- Al buscar (login, recuperación, duplicados), se compara normalizado,
  incluyendo cuentas antiguas guardadas en otros formatos.
"""
import phonenumbers

REGION_POR_DEFECTO = 'CO'


def normalizar_telefono(valor):
    """
    Retorna el teléfono en formato E.164 (ej. '+573001234567'),
    o None si no se puede interpretar como un número posible.
    """
    if not valor:
        return None
    try:
        numero = phonenumbers.parse(str(valor), REGION_POR_DEFECTO)
    except phonenumbers.NumberParseException:
        return None
    if not phonenumbers.is_possible_number(numero):
        return None
    return phonenumbers.format_number(numero, phonenumbers.PhoneNumberFormat.E164)


def filtrar_por_telefono(queryset, valor, campo='telefono'):
    """
    Registros del queryset cuyo teléfono corresponde al mismo número que `valor`,
    sin importar el formato en que se guardó.

    Primero busca coincidencias exactas (rápido, datos ya normalizados);
    si no hay, compara normalizando cada registro, para cubrir datos antiguos
    guardados con espacios, guiones o sin código de país.
    """
    normalizado = normalizar_telefono(valor)
    if not normalizado:
        return list(queryset.filter(**{campo: str(valor).strip()}))

    exactos = list(queryset.filter(**{f'{campo}__in': {normalizado, str(valor).strip()}}))
    if exactos:
        return exactos

    # Datos antiguos en otro formato: normalizar cada uno y comparar.
    # Las tablas de usuarios y registros son pequeñas (dueños de negocio).
    ids = [
        pk for pk, telefono in queryset.values_list('pk', campo)
        if normalizar_telefono(telefono) == normalizado
    ]
    return list(queryset.filter(pk__in=ids)) if ids else []


def telefono_registrado(queryset, valor, campo='telefono'):
    """True si el número ya existe en el queryset, en cualquier formato"""
    return bool(filtrar_por_telefono(queryset, valor, campo))
