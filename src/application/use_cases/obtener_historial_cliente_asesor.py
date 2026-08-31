from typing import List

from src.domain.ports.llamada_repository import LlamadaRepository


class ObtenerHistorialClienteAsesor:
    """
    Historial de novedades de un cliente, visible sólo para la asesora
    que las registró (BR-012) — a diferencia de ObtenerHistorial (usado
    en la cola), este no expone novedades de otras asesoras y sí incluye
    las anuladas (marcadas, no ocultas).
    """

    def __init__(self, llamada_repo: LlamadaRepository):
        self._llamada_repo = llamada_repo

    async def execute(self, cliente_id: str, asesor: str) -> List[dict]:
        return await self._llamada_repo.get_historial_novedades_por_asesor(cliente_id, asesor)
