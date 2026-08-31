from datetime import time
from typing import Optional


def esta_fuera_de_franja(
    franja_desde: Optional[time], franja_hasta: Optional[time], ahora: time
) -> Optional[bool]:
    """
    Compara la hora actual contra la franja horaria preferida del cliente.

    Devuelve:
      None  → sin preferencia registrada (ambas vacías, o solo una —
              un dato incompleto se trata igual que "sin preferencia",
              nunca genera un aviso ni rompe nada).
      True  → la hora actual está FUERA de la franja.
      False → la hora actual está DENTRO de la franja.

    `ahora` debe venir ya en hora de Colombia (ver ahora_colombia()) —
    esta función no conoce zonas horarias, solo compara horas del reloj.

    Franjas que cruzan medianoche (ej. 22:00-02:00) se tratan como un
    rango que "envuelve": se está dentro si la hora es >= franja_desde
    O <= franja_hasta. No es el caso de uso real (llamadas comerciales
    diurnas) pero se cubre para que un dato así nunca produzca un
    resultado incorrecto o una excepción.
    """
    if franja_desde is None or franja_hasta is None:
        return None

    if franja_desde <= franja_hasta:
        dentro = franja_desde <= ahora <= franja_hasta
    else:
        dentro = ahora >= franja_desde or ahora <= franja_hasta

    return not dentro
