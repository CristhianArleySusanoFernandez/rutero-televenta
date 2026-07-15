from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class SesionTelefono:
    """Estado efímero de un teléfono conectado por WebSocket. No se persiste en BD."""

    telefono_id: str
    conectado: bool = True
    disponible: bool = False        # True tras recibir 'disponible'
    en_llamada: bool = False        # True mientras hay OFFHOOK sin IDLE
    llamada_activa_id: Optional[str] = None  # UUID de la llamada en curso
    bateria: Optional[int] = None
    cargando: Optional[bool] = None
    modelo: Optional[str] = None
    android_version: Optional[str] = None
    app_version: Optional[str] = None
    ultimo_mensaje: datetime = field(default_factory=datetime.utcnow)

    def actualizar_salud(self, bateria: int, cargando: bool, en_llamada: bool) -> None:
        self.bateria = bateria
        self.cargando = cargando
        self.en_llamada = en_llamada
        self.ultimo_mensaje = datetime.utcnow()

    def marcar_disponible(self) -> None:
        self.disponible = True
        self.en_llamada = False
        self.llamada_activa_id = None
        self.ultimo_mensaje = datetime.utcnow()

    def iniciar_llamada(self, llamada_id: str) -> None:
        self.disponible = False
        self.en_llamada = True
        self.llamada_activa_id = llamada_id
        self.ultimo_mensaje = datetime.utcnow()

    def finalizar_llamada(self) -> None:
        self.en_llamada = False
        self.llamada_activa_id = None
        self.ultimo_mensaje = datetime.utcnow()

    def segundos_sin_mensaje(self) -> float:
        return (datetime.utcnow() - self.ultimo_mensaje).total_seconds()

    def to_dict(self) -> dict:
        return {
            "telefono_id": self.telefono_id,
            "conectado": self.conectado,
            "disponible": self.disponible,
            "en_llamada": self.en_llamada,
            "llamada_activa_id": self.llamada_activa_id,
            "bateria": self.bateria,
            "cargando": self.cargando,
            "modelo": self.modelo,
            "android_version": self.android_version,
            "app_version": self.app_version,
            "segundos_sin_mensaje": round(self.segundos_sin_mensaje()),
        }
