from datetime import date, datetime, timezone, timedelta

try:
    from zoneinfo import ZoneInfo

    _COLOMBIA = ZoneInfo("America/Bogota")
except Exception:
    # Sin base de datos de zonas horarias disponible: Colombia no tiene
    # horario de verano, así que un offset fijo -5 es equivalente.
    _COLOMBIA = timezone(timedelta(hours=-5))


def hoy_colombia() -> date:
    """Fecha calendario actual en hora de Colombia (UTC-5, sin horario de verano)."""
    return datetime.now(_COLOMBIA).date()


def ahora_colombia() -> datetime:
    """Fecha y hora actuales en hora de Colombia (UTC-5, sin horario de verano)."""
    return datetime.now(_COLOMBIA)


_DIAS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
_MESES_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def fecha_larga_es(fecha: date) -> str:
    """
    Fecha larga en español (ej. "Lunes 31 de agosto de 2026"), con nombres
    de día/mes definidos explícitamente — NO depende del locale del
    sistema operativo, que en Render corre en inglés y produciría
    "Monday 31 de august de 2026" con strftime('%A'/'%B').
    """
    dia_semana = _DIAS_ES[fecha.weekday()]
    mes = _MESES_ES[fecha.month - 1]
    return f"{dia_semana} {fecha.day} de {mes} de {fecha.year}"
