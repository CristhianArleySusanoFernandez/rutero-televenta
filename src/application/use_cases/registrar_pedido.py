from datetime import date
from typing import Optional

from src.domain.entities.pedido import Pedido
from src.domain.ports.pedido_repository import PedidoRepository
from src.domain.servicios.fecha_colombia import hoy_colombia


class RegistrarPedido:
    """
    Registra lo vendido en una llamada. No cambia el estado del cliente
    en la cola ni crea novedades — es un dato aparte, permanente del
    cliente, independiente del resultado de la llamada.
    """

    def __init__(self, pedido_repo: PedidoRepository):
        self._pedido_repo = pedido_repo

    async def execute(
        self,
        cliente_id: str,
        detalle: str,
        asesor: str,
        rutero_cliente_id: Optional[str] = None,
        fecha: Optional[date] = None,
    ) -> Pedido:
        detalle_limpio = " ".join(detalle.split())
        if not detalle_limpio:
            raise ValueError("El detalle del pedido no puede quedar vacío")

        pedido = Pedido(
            cliente_id=cliente_id,
            fecha=fecha or hoy_colombia(),
            detalle=detalle_limpio,
            rutero_cliente_id=rutero_cliente_id,
            asesor=asesor,
        )
        return await self._pedido_repo.crear(pedido)
