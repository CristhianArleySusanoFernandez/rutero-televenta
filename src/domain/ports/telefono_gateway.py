from abc import ABC, abstractmethod
from typing import Optional

from src.domain.entities.sesion_telefono import SesionTelefono


class TelefonoGateway(ABC):
    """
    Puerto de salida: canal hacia el teléfono físico del asesor.

    La aplicación llama a este puerto para ordenar llamadas/colgar.
    La implementación concreta (WebSocket) vive en infrastructure/adapters/.
    """

    @abstractmethod
    async def ordenar_llamada(
        self,
        telefono_id: str,
        llamada_id: str,
        numero: str,
        nombre_contacto: Optional[str] = None,
    ) -> None:
        """Envía mensaje 'llamar' al teléfono. Lanza RuntimeError si no está disponible."""

    @abstractmethod
    async def ordenar_colgar(self, telefono_id: str, llamada_id: str) -> None:
        """Envía mensaje 'colgar' al teléfono."""

    @abstractmethod
    def get_sesion(self, telefono_id: str) -> Optional[SesionTelefono]:
        """Devuelve el estado actual del teléfono en memoria, o None si no está conectado."""

    @abstractmethod
    def listar_sesiones(self) -> list[SesionTelefono]:
        """Devuelve todas las sesiones activas."""
