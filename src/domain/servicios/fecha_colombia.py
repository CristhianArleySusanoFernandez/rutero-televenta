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
