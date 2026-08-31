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
    async def buscar(self, termino: str, limite: int = 50) -> List[Cliente]:
        """
        Busca clientes cuyo nombre, razón social o teléfono contengan el
        término (parcial, insensible a mayúsculas). Tabla global, no
        particionada por asesor — la búsqueda puede devolver clientes de
        cualquier asesora; el aislamiento (BR-012) se aplica después, al
        leer el historial de novedades, no aquí.
        """
        ...

    @abstractmethod
    async def actualizar(self, cliente_id: str, datos: dict) -> Cliente:
        """
        Actualiza SOLO los campos editables de un cliente: nombre,
        razon_social, direccion, barrio, ciudad, telefono, documento.
        `datos` trae únicamente esas claves (ya validadas por el caso de
        uso) — nunca cod_cliente ni dias_visita, que no son editables.
        """
        ...

    @abstractmethod
    async def get_by_cod(self, cod_cliente: str) -> Optional[Cliente]:
        ...

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[Cliente]:
        ...
