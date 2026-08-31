from datetime import date
from typing import List

from supabase import Client

from src.domain.entities.cambio_cliente import CambioCliente
from src.domain.ports.cambio_cliente_repository import CambioClienteRepository


class SupabaseCambioClienteRepository(CambioClienteRepository):
    def __init__(self, client: Client):
        self._db = client

    async def crear_lote(self, cambios: List[CambioCliente]) -> None:
        if not cambios:
            return
        filas = [
            {
                "cliente_id": c.cliente_id,
                "asesor": c.asesor,
                "campo": c.campo,
                "valor_anterior": c.valor_anterior,
                "valor_nuevo": c.valor_nuevo,
                "fecha": str(c.fecha),
            }
            for c in cambios
        ]
        self._db.table("cambios_cliente").insert(filas).execute()

    async def get_por_cliente(self, cliente_id: str) -> List[CambioCliente]:
        result = (
            self._db.table("cambios_cliente")
            .select("*")
            .eq("cliente_id", cliente_id)
            .order("created_at", desc=True)
            .execute()
        )
        return [self._to_entity(row) for row in (result.data or [])]

    async def get_por_asesor_rango(self, asesor: str, desde: date, hasta: date) -> List[dict]:
        result = (
            self._db.table("cambios_cliente")
            .select("campo, valor_anterior, valor_nuevo, asesor, fecha, clientes(cod_cliente, nombre)")
            .eq("asesor", asesor)
            .gte("fecha", str(desde))
            .lte("fecha", str(hasta))
            .order("fecha")
            .execute()
        )
        filas = []
        for row in (result.data or []):
            cliente = row.get("clientes") or {}
            filas.append({
                "cod_cliente": cliente.get("cod_cliente"),
                "nombre": cliente.get("nombre"),
                "campo": row.get("campo"),
                "valor_anterior": row.get("valor_anterior"),
                "valor_nuevo": row.get("valor_nuevo"),
                "asesor": row.get("asesor"),
                "fecha": row.get("fecha"),
            })
        # PostgREST no ordena de forma sencilla por una columna de la
        # tabla enlazada (clientes.nombre); se ordena aquí en Python —
        # el volumen (correcciones de un asesor en una semana) es chico.
        filas.sort(key=lambda f: (f["fecha"] or "", f["nombre"] or ""))
        return filas

    def _to_entity(self, row: dict) -> CambioCliente:
        return CambioCliente(
            id=row["id"],
            cliente_id=row["cliente_id"],
            asesor=row.get("asesor"),
            campo=row["campo"],
            valor_anterior=row.get("valor_anterior"),
            valor_nuevo=row.get("valor_nuevo"),
            fecha=row["fecha"],
            created_at=row.get("created_at"),
        )
