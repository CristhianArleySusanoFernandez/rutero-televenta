from typing import List

from src.domain.entities.pedido import Pedido
from src.domain.ports.pedido_repository import PedidoRepository

MAX_PEDIDOS_HISTORIAL = 3


class ObtenerHistorialPedidosCliente:
    """Últimos pedidos de un cliente, para la ficha del buscador."""

    def __init__(self, pedido_repo: PedidoRepository):
        self._pedido_repo = pedido_repo

    async def execute(self, cliente_id: str) -> List[Pedido]:
        return await self._pedido_repo.get_ultimos_por_cliente(cliente_id, MAX_PEDIDOS_HISTORIAL)
