from typing import List

from supabase import Client

from src.domain.entities.nota_cliente import NotaCliente
from src.domain.ports.nota_cliente_repository import NotaClienteRepository


class SupabaseNotaClienteRepository(NotaClienteRepository):
    def __init__(self, client: Client):
        self._db = client

    async def agregar(self, nota: NotaCliente) -> NotaCliente:
        result = (
            self._db.table("notas_cliente")
            .insert({"cliente_id": nota.cliente_id, "nota": nota.nota, "autor": nota.autor})
            .execute()
        )
        row = result.data[0]
        nota.id = row["id"]
        nota.created_at = row.get("created_at")
        return nota

    async def listar_por_cliente(self, cliente_id: str) -> List[NotaCliente]:
        result = (
            self._db.table("notas_cliente")
            .select("*")
            .eq("cliente_id", cliente_id)
            .order("created_at", desc=False)
            .execute()
        )
        return [self._to_entity(r) for r in (result.data or [])]

    async def eliminar(self, nota_id: str) -> None:
        self._db.table("notas_cliente").delete().eq("id", nota_id).execute()

    def _to_entity(self, row: dict) -> NotaCliente:
        return NotaCliente(
            id=row["id"],
            cliente_id=row["cliente_id"],
            nota=row["nota"],
            autor=row.get("autor"),
            created_at=row.get("created_at"),
        )
