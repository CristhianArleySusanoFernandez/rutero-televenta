from enum import Enum


class TipoNovedad(str, Enum):
    NO_CONTESTO = "No contestó"
    NEGOCIO_CERRADO = "Negocio cerrado"
    CAMBIO_DUENO = "Cambió de dueño"
    NUMERO_EQUIVOCADO = "Número equivocado / no existe"
    CLIENTE_NO_QUIERE = "Cliente no quiere ser llamado"
    DIRECCION_INCORRECTA = "Dirección incorrecta"
    SIN_INTERES = "No tiene interés en productos"
    OTRO = "Otro (ver observación)"
