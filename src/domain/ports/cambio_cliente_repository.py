from abc import ABC, abstractmethod
from datetime import date
from typing import List

from src.domain.entities.cambio_cliente import CambioCliente


class CambioClienteRepository(ABC):
    """
    Puerto propio (no se amplía ClienteRepository): igual criterio que
    `PedidoRepository`/`NotaClienteRepository` — `cambios_cliente` es una
    tabla y un ciclo de vida propios (historial de auditoría), no datos
    del cliente en sí.
    """

    @abstractmethod
    async def crear_lote(self, cambios: List[CambioCliente]) -> None:
        """Inserta varias filas de una vez (un guardado puede tocar varios campos)."""
        ...

    @abstractmethod
    async def get_por_cliente(self, cliente_id: str) -> List[CambioCliente]:
        """Historial de cambios del cliente, más reciente primero."""
        ...

    @abstractmethod
    async def get_por_asesor_rango(self, asesor: str, desde: date, hasta: date) -> List[dict]:
        """
        Cambios de UN asesor (BR-012: nunca de otro) en el rango [desde,
        hasta] (ambos inclusive), con 'cod_cliente' y 'nombre' del cliente
        ya resueltos (join), para que el reporte no tenga que hacer una
        consulta aparte por cada fila. Ordenado por fecha y luego cliente.
        Claves del dict: cod_cliente, nombre, campo, valor_anterior,
        valor_nuevo, asesor, fecha.
        """
        ...
