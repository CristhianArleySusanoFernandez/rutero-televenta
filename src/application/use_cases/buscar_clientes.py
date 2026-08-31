from typing import List

from src.domain.entities.cliente import Cliente
from src.domain.ports.cliente_repository import ClienteRepository

MIN_CARACTERES = 3
LIMITE_RESULTADOS = 50


class BuscarClientes:
    """Búsqueda de clientes por nombre, razón social o teléfono, fuera de la cola."""

    def __init__(self, cliente_repo: ClienteRepository):
        self._cliente_repo = cliente_repo

    async def execute(self, termino: str) -> List[Cliente]:
        termino_limpio = termino.strip()
        if len(termino_limpio) < MIN_CARACTERES:
            return []
        return await self._cliente_repo.buscar(termino_limpio, limite=LIMITE_RESULTADOS)
