import logging

from src.domain.ports.llamada_repository import LlamadaRepository

log = logging.getLogger(__name__)


class RegistrarFinLlamada:
    """
    Guarda la duración cuando el teléfono reporta IDLE.

    Se invoca desde el hook on_llamada_finalizada del gateway
    (cableado en la capa de composición), no desde un endpoint HTTP.
    """

    def __init__(self, llamada_repo: LlamadaRepository):
        self._repo = llamada_repo

    async def execute(self, llamada_id: str, duracion_seg: int) -> None:
        if not llamada_id:
            return
        try:
            await self._repo.guardar_duracion_llamada(llamada_id, duracion_seg)
            log.info(
                "Duración guardada — llamada_id=%s duración=%ss",
                llamada_id, duracion_seg,
            )
        except Exception:
            # El IDLE ya ocurrió; fallar aquí no debe tumbar la conexión WebSocket.
            log.exception("Error guardando duración de llamada_id=%s", llamada_id)
