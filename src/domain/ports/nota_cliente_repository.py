from abc import ABC, abstractmethod
from typing import List

from src.domain.entities.nota_cliente import NotaCliente


class NotaClienteRepository(ABC):
    @abstractmethod
    async def agregar(self, nota: NotaCliente) -> NotaCliente:
        ...

    @abstractmethod
    async def listar_por_cliente(self, cliente_id: str) -> List[NotaCliente]:
        ...

    @abstractmethod
    async def eliminar(self, nota_id: str) -> None:
        ...
