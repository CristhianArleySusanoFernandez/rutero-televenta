from typing import List

from supabase import Client

from src.domain.entities.pedido import Pedido
from src.domain.ports.pedido_repository import PedidoRepository


class SupabasePedidoRepository(PedidoRepository):
    def __init__(self, client: Client):
        self._db = client

    async def crear(self, pedido: Pedido) -> Pedido:
        result = (
            self._db.table("pedidos")
            .insert({
                "cliente_id": pedido.cliente_id,
                "rutero_cliente_id": pedido.rutero_cliente_id,
                "asesor": pedido.asesor,
                "fecha": str(pedido.fecha),
                "detalle": pedido.detalle,
            })
            .execute()
        )
        row = result.data[0]
        pedido.id = row["id"]
        pedido.created_at = row.get("created_at")
        return pedido

    async def get_ultimos_por_cliente(self, cliente_id: str, limite: int = 3) -> List[Pedido]:
        result = (
            self._db.table("pedidos")
            .select("*")
            .eq("cliente_id", cliente_id)
            .order("fecha", desc=True)
            .order("created_at", desc=True)
            .limit(limite)
            .execute()
        )
        return [self._to_entity(row) for row in (result.data or [])]

    async def get_detalles_recientes_cliente(self, cliente_id: str, limite: int) -> List[str]:
        result = (
            self._db.table("pedidos")
            .select("detalle")
            .eq("cliente_id", cliente_id)
            .order("created_at", desc=True)
            .limit(limite * 5)
            .execute()
        )
        vistos: List[str] = []
        for row in (result.data or []):
            detalle = row.get("detalle")
            if detalle and detalle not in vistos:
                vistos.append(detalle)
            if len(vistos) >= limite:
                break
        return vistos

    async def get_detalles_recientes_asesor(self, asesor: str, limite: int) -> List[str]:
        result = (
            self._db.table("pedidos")
            .select("detalle")
            .eq("asesor", asesor)
            .order("created_at", desc=True)
            .limit(limite)
            .execute()
        )
        return [row["detalle"] for row in (result.data or []) if row.get("detalle")]

    def _to_entity(self, row: dict) -> Pedido:
        return Pedido(
            id=row["id"],
            cliente_id=row["cliente_id"],
            fecha=row["fecha"],
            detalle=row["detalle"],
            rutero_cliente_id=row.get("rutero_cliente_id"),
            asesor=row.get("asesor"),
            created_at=row.get("created_at"),
        )
