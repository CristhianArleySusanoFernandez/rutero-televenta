from collections import Counter
from typing import List

from src.domain.ports.pedido_repository import PedidoRepository

MAX_SUGERENCIAS_CLIENTE = 5
MAX_SUGERENCIAS_TOTAL = 10
# Ventana de pedidos recientes del asesor sobre la que se calcula
# frecuencia — acotada para no traer el historial completo si el asesor
# lleva mucho tiempo usando la app. Con este volumen (cientos de
# pedidos), calcular la frecuencia en Python es barato; si la tabla
# creciera a decenas de miles de filas por asesor, esto debería
# resolverse de otra forma (agregación en la base, no en Python).
VENTANA_PEDIDOS_ASESOR = 300


class ObtenerSugerenciasPedido:
    """
    Sugerencias de texto para el campo de detalle del pedido: primero lo
    que ese mismo cliente ya compró antes (más reciente primero), luego
    lo más frecuente de la asesora en general — para que los nombres
    converjan con el tiempo sin imponer un catálogo.
    """

    def __init__(self, pedido_repo: PedidoRepository):
        self._pedido_repo = pedido_repo

    async def execute(self, cliente_id: str, asesor: str) -> List[str]:
        del_cliente = await self._pedido_repo.get_detalles_recientes_cliente(
            cliente_id, MAX_SUGERENCIAS_CLIENTE
        )

        detalles_asesor = await self._pedido_repo.get_detalles_recientes_asesor(
            asesor, VENTANA_PEDIDOS_ASESOR
        )
        frecuencia = Counter(detalles_asesor)
        del_asesor_ordenado = [detalle for detalle, _ in frecuencia.most_common()]

        sugerencias: List[str] = list(del_cliente)
        for detalle in del_asesor_ordenado:
            if len(sugerencias) >= MAX_SUGERENCIAS_TOTAL:
                break
            if detalle not in sugerencias:
                sugerencias.append(detalle)

        return sugerencias[:MAX_SUGERENCIAS_TOTAL]
