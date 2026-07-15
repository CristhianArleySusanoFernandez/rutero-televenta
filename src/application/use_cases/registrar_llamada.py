from src.domain.ports.llamada_repository import LlamadaRepository
from src.domain.value_objects.estado_llamada import EstadoLlamada


class RegistrarLlamada:
    def __init__(self, llamada_repo: LlamadaRepository):
        self._llamada_repo = llamada_repo

    async def execute(self, rutero_cliente_id: str, estado: EstadoLlamada) -> dict:
        llamada = await self._llamada_repo.actualizar_estado(rutero_cliente_id, estado)
        return {"id": llamada.id, "estado": llamada.estado}
