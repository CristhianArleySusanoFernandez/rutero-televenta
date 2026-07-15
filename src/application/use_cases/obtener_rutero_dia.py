from datetime import date
from typing import List

from src.domain.ports.llamada_repository import LlamadaRepository


class ObtenerRuteroDia:
    def __init__(self, llamada_repo: LlamadaRepository):
        self._llamada_repo = llamada_repo

    async def execute(self, fecha: date) -> List[dict]:
        return await self._llamada_repo.get_llamadas_del_dia(fecha)
