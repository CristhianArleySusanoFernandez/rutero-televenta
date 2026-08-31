from typing import List, Optional

from supabase import Client

from src.domain.ports.asesor_repository import AsesorRepository


class SupabaseAsesorRepository(AsesorRepository):
    def __init__(self, client: Client):
        self._db = client

    async def listar_nombres(self) -> List[str]:
        de_tabla = self._db.table("asesores").select("nombre").execute()
        de_ruteros = (
            self._db.table("rutero_dias")
            .select("asesor")
            .not_.is_("asesor", "null")
            .execute()
        )
        nombres = {row["nombre"] for row in de_tabla.data}
        nombres.update(row["asesor"] for row in de_ruteros.data if row["asesor"])
        return sorted(nombres)

    async def crear_si_no_existe(self, nombre: str) -> None:
        existente = (
            self._db.table("asesores").select("nombre").eq("nombre", nombre).limit(1).execute()
        )
        if not existente.data:
            self._db.table("asesores").insert({"nombre": nombre}).execute()

    async def get_telefono_id(self, nombre: str) -> Optional[str]:
        result = (
            self._db.table("asesores")
            .select("telefono_id")
            .eq("nombre", nombre)
            .limit(1)
            .execute()
        )
        return result.data[0]["telefono_id"] if result.data else None

    async def set_telefono_id(self, nombre: str, telefono_id: str) -> None:
        self._db.table("asesores").upsert({"nombre": nombre, "telefono_id": telefono_id}).execute()

    async def get_codigo_asesor(self, nombre: str) -> Optional[str]:
        result = (
            self._db.table("asesores")
            .select("codigo_asesor")
            .eq("nombre", nombre)
            .limit(1)
            .execute()
        )
        return result.data[0]["codigo_asesor"] if result.data else None

    async def set_codigo_asesor(self, nombre: str, codigo_asesor: str) -> None:
        self._db.table("asesores").upsert({"nombre": nombre, "codigo_asesor": codigo_asesor}).execute()
