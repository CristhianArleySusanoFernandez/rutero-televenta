from abc import ABC, abstractmethod
from typing import List

from src.domain.entities.pedido import Pedido


class PedidoRepository(ABC):
    """
    Puerto propio (no se amplía LlamadaRepository ni ClienteRepository):
    `pedidos` es una tabla y un ciclo de vida propios, igual que
    `notas_cliente` tiene su `NotaClienteRepository` dedicado — mantiene
    los puertos existentes del tamaño que tienen y evita mezclar
    conceptos (un pedido no es una llamada ni una novedad).
    """

    @abstractmethod
    async def crear(self, pedido: Pedido) -> Pedido:
        ...

    @abstractmethod
    async def get_ultimos_por_cliente(self, cliente_id: str, limite: int = 3) -> List[Pedido]:
        """Últimos `limite` pedidos del cliente, más reciente primero."""
        ...

    @abstractmethod
    async def get_detalles_recientes_cliente(self, cliente_id: str, limite: int) -> List[str]:
        """
        Detalles distintos ya registrados para ESTE cliente, más reciente
        primero — para sugerencias con prioridad a lo ya dicho por él.
        """
        ...

    @abstractmethod
    async def get_detalles_recientes_asesor(self, asesor: str, limite: int) -> List[str]:
        """
        Detalles (con repetición) de los pedidos más recientes de este
        asesor, sin filtrar por cliente — la frecuencia se calcula en el
        caso de uso, en Python, sobre esta lista ya acotada.
        """
        ...
