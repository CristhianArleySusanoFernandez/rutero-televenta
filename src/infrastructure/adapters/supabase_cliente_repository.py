from typing import Optional

from supabase import Client

from src.domain.entities.cliente import Cliente
from src.domain.ports.cliente_repository import ClienteRepository


class SupabaseClienteRepository(ClienteRepository):
    def __init__(self, client: Client):
        self._db = client

    async def upsert(self, cliente: Cliente) -> Cliente:
        data = {
            "cod_cliente": cliente.cod_cliente,
            "nombre": cliente.nombre,
            "documento": cliente.documento,
            "razon_social": cliente.razon_social,
            "direccion": cliente.direccion,
            "barrio": cliente.barrio,
            "ciudad": cliente.ciudad,
            "dias_visita": cliente.dias_visita,
            "telefono": cliente.telefono,
        }
        result = (
            self._db.table("clientes")
            .upsert(data, on_conflict="cod_cliente")
            .execute()
        )
        row = result.data[0]
        return self._to_entity(row)

    async def get_by_cod(self, cod_cliente: str) -> Optional[Cliente]:
        result = (
            self._db.table("clientes")
            .select("*")
            .eq("cod_cliente", cod_cliente)
            .limit(1)
            .execute()
        )
        if not result.data:
            return None
        return self._to_entity(result.data[0])

    async def get_by_id(self, id: str) -> Optional[Cliente]:
        result = (
            self._db.table("clientes")
            .select("*")
            .eq("id", id)
            .limit(1)
            .execute()
        )
        if not result.data:
            return None
        return self._to_entity(result.data[0])

    def _to_entity(self, row: dict) -> Cliente:
        return Cliente(
            id=row["id"],
            cod_cliente=row["cod_cliente"],
            nombre=row["nombre"],
            documento=row.get("documento"),
            razon_social=row.get("razon_social"),
            direccion=row.get("direccion"),
            barrio=row.get("barrio"),
            ciudad=row.get("ciudad"),
            dias_visita=row.get("dias_visita"),
            telefono=row.get("telefono"),
        )
