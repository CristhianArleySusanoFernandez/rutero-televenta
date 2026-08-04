from typing import List

from src.domain.ports.asesor_repository import AsesorRepository


class ListarAsesores:
    def __init__(self, asesor_repo: AsesorRepository):
        self._asesor_repo = asesor_repo

    async def execute(self) -> List[str]:
        return await self._asesor_repo.listar_nombres()
