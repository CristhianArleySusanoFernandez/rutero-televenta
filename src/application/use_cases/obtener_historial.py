from typing import List

from src.domain.entities.novedad import Novedad
from src.domain.ports.llamada_repository import LlamadaRepository


class ObtenerHistorial:
    def __init__(self, llamada_repo: LlamadaRepository):
        self._llamada_repo = llamada_repo

    async def execute(self, cliente_id: str) -> List[Novedad]:
        return await self._llamada_repo.get_historial_novedades(cliente_id)
