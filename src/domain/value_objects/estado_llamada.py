from enum import Enum


class EstadoLlamada(str, Enum):
    """Resultado de la llamada. Una novedad es independiente de esto (ver entities.novedad)."""

    PENDIENTE = "pendiente"
    REINTENTO_PENDIENTE = "reintento_pendiente"
    REAGENDADO = "reagendado"
    CONTESTO = "contesto"
    NO_CONTESTO = "no_contesto"
    # Ya no se asigna: la constraint de la tabla la sigue permitiendo por
    # compatibilidad con datos históricos, pero ninguna ruta de código la escribe.
    NOVEDAD = "novedad"
