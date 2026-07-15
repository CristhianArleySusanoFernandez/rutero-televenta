from enum import Enum


class EstadoLlamada(str, Enum):
    PENDIENTE = "pendiente"
    REINTENTO_PENDIENTE = "reintento_pendiente"
    REAGENDADO = "reagendado"
    CONTESTO = "contesto"
    NO_CONTESTO = "no_contesto"
    NOVEDAD = "novedad"
