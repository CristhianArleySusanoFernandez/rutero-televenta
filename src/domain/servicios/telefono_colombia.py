from typing import Optional

LONGITUD_MOVIL_COLOMBIA = 10
PREFIJO_PAIS = "57"


def normalizar_telefono_whatsapp(numero) -> Optional[str]:
    """
    Convierte un teléfono colombiano (ej. '317 433-2292') al formato que
    espera wa.me: solo dígitos, con el 57 de país antepuesto.
    Devuelve None si no alcanza a ser un móvil colombiano válido (10
    dígitos sin el indicativo) — nunca inventa ni corrige un número raro.
    """
    if not numero:
        return None

    solo_digitos = "".join(c for c in str(numero) if c.isdigit())

    if len(solo_digitos) == LONGITUD_MOVIL_COLOMBIA:
        return PREFIJO_PAIS + solo_digitos

    if len(solo_digitos) == LONGITUD_MOVIL_COLOMBIA + len(PREFIJO_PAIS) and solo_digitos.startswith(PREFIJO_PAIS):
        return solo_digitos

    return None
