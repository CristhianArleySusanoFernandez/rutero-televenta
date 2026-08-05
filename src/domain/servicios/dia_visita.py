from datetime import date, timedelta
from typing import Optional

# Últimos 2 caracteres del código de "Dias Visita" (sin espacios, mayúsculas).
# Los prefijos de frecuencia (SS=semanal, Q=quincenal, M=mensual) se ignoran.
_DIAS = {"LU": 0, "MA": 1, "MI": 2, "JU": 3, "VI": 4, "SA": 5}


def parsear_dia_visita(codigo: Optional[str]) -> Optional[int]:
    """
    0=lunes .. 5=sábado, o None si el código no termina en un día válido.
    Tolerante a espacios: "SS MI" y "SSMI" dan lo mismo.
    """
    if not codigo:
        return None
    limpio = codigo.replace(" ", "").upper()
    return _DIAS.get(limpio[-2:])


def fecha_del_dia_en_semana(fecha_ancla: date, dia_semana: int) -> date:
    """Fecha calendario del día indicado (0=lunes..5=sábado) en la misma semana que fecha_ancla."""
    lunes = fecha_ancla - timedelta(days=fecha_ancla.weekday())
    return lunes + timedelta(days=dia_semana)
