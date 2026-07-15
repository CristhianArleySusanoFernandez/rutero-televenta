from typing import List

from src.domain.entities.nota_cliente import NotaCliente
from src.domain.ports.nota_cliente_repository import NotaClienteRepository


class GestionarNotasCliente:
    def __init__(self, repo: NotaClienteRepository):
        self._repo = repo

    async def agregar(self, cliente_id: str, nota: str, autor: str | None) -> NotaCliente:
        nueva = NotaCliente(cliente_id=cliente_id, nota=nota, autor=autor)
        return await self._repo.agregar(nueva)

    async def listar(self, cliente_id: str) -> List[NotaCliente]:
        return await self._repo.listar_por_cliente(cliente_id)

    async def eliminar(self, nota_id: str) -> None:
        await self._repo.eliminar(nota_id)
