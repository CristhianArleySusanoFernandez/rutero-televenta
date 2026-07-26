from abc import ABC, abstractmethod
from typing import Optional

from src.domain.entities.cliente import Cliente


class ClienteRepository(ABC):
    @abstractmethod
    async def upsert(self, cliente: Cliente) -> Cliente:
        ...

    @abstractmethod
    async def get_by_cod(self, cod_cliente: str) -> Optional[Cliente]:
        ...

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[Cliente]:
        ...
