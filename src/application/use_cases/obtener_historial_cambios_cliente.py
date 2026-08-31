from typing import List

from src.domain.entities.cambio_cliente import CambioCliente
from src.domain.ports.cambio_cliente_repository import CambioClienteRepository


class ObtenerHistorialCambiosCliente:
    """Historial de correcciones de datos de un cliente, para la ficha del buscador."""

    def __init__(self, cambio_repo: CambioClienteRepository):
        self._cambio_repo = cambio_repo

    async def execute(self, cliente_id: str) -> List[CambioCliente]:
        return await self._cambio_repo.get_por_cliente(cliente_id)
