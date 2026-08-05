from datetime import date

from src.domain.ports.llamada_repository import LlamadaRepository


class EliminarRuteroDia:
    def __init__(self, llamada_repo: LlamadaRepository):
        self._llamada_repo = llamada_repo

    async def resumen(self, fecha: date, asesor: str) -> dict:
        return await self._llamada_repo.contar_rutero_dia(fecha, asesor)

    async def execute(self, fecha: date, asesor: str) -> bool:
        return await self._llamada_repo.eliminar_rutero_dia(fecha, asesor)
