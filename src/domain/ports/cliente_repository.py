from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.entities.cliente import Cliente


class ClienteRepository(ABC):
    @abstractmethod
    async def upsert(self, cliente: Cliente) -> Cliente:
        ...

    @abstractmethod
    async def upsert_lote(self, clientes: List[Cliente]) -> dict[str, str]:
        """
        Upsert masivo (merge por cod_cliente, igual que upsert()).
        Devuelve el mapa {cod_cliente: id} de todos los clientes del lote.
        """
        ...

    @abstractmethod
    async def get_by_cod(self, cod_cliente: str) -> Optional[Cliente]:
        ...

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[Cliente]:
        ...
