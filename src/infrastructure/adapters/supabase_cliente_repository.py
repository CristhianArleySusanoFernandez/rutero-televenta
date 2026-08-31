from typing import List, Optional

from supabase import Client

from src.domain.entities.cliente import Cliente
from src.domain.ports.cliente_repository import ClienteRepository


class SupabaseClienteRepository(ClienteRepository):
    def __init__(self, client: Client):
        self._db = client

    def _to_row(self, cliente: Cliente) -> dict:
        return {
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

    async def upsert(self, cliente: Cliente) -> Cliente:
        data = self._to_row(cliente)
        result = (
            self._db.table("clientes")
            .upsert(data, on_conflict="cod_cliente")
            .execute()
        )
        row = result.data[0]
        return self._to_entity(row)

    async def upsert_lote(self, clientes: List[Cliente]) -> dict[str, str]:
        if not clientes:
            return {}
        data = [self._to_row(c) for c in clientes]
        # Sin ignore_duplicates: merge por cod_cliente, igual que upsert()
        # individual — PostgREST devuelve TODAS las filas (insertadas y
        # actualizadas) porque ON CONFLICT DO UPDATE siempre retorna la fila.
        result = (
            self._db.table("clientes")
            .upsert(data, on_conflict="cod_cliente")
            .execute()
        )
        # cod_cliente viene TEXT en la base pero puede llegar numérico desde
        # el Excel — se normaliza a str para que las claves del mapa calcen
        # con las que use quien lo consulte.
        return {str(row["cod_cliente"]): row["id"] for row in result.data}

    async def buscar(self, termino: str, limite: int = 50) -> List[Cliente]:
        # Se quitan comas y paréntesis: son separadores de condición en la
        # sintaxis .or_() de PostgREST y romperían el filtro si el término
        # los trae (ej. teléfonos escritos "(123) 456").
        termino_normalizado = " ".join(termino.split()).replace(",", "").replace("(", "").replace(")", "")
        termino_telefono = termino_normalizado.replace(" ", "")
        patron = f"%{termino_normalizado}%"
        patron_telefono = f"%{termino_telefono}%"
        result = (
            self._db.table("clientes")
            .select("*")
            .or_(
                f"nombre.ilike.{patron},"
                f"razon_social.ilike.{patron},"
                f"telefono.ilike.{patron_telefono}"
            )
            .limit(limite)
            .execute()
        )
        return [self._to_entity(row) for row in (result.data or [])]

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
