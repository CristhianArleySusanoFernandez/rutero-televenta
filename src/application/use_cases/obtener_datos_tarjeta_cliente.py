from src.domain.ports.llamada_repository import LlamadaRepository


class ObtenerDatosTarjetaCliente:
    def __init__(self, llamada_repo: LlamadaRepository):
        self._llamada_repo = llamada_repo

    async def execute(self, rutero_cliente_id: str) -> dict:
        return await self._llamada_repo.get_datos_tarjeta_cliente(rutero_cliente_id)
