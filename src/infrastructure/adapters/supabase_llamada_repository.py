from datetime import date, datetime, timezone, timedelta
from typing import List, Optional

from supabase import Client

from src.domain.entities.llamada import Llamada
from src.domain.entities.novedad import Novedad
from src.domain.ports.llamada_repository import LlamadaRepository
from src.domain.value_objects.estado_llamada import EstadoLlamada
from src.domain.value_objects.tipo_novedad import TipoNovedad


class SupabaseLlamadaRepository(LlamadaRepository):
    def __init__(self, client: Client):
        self._db = client

    async def crear_rutero_dia(self, fecha: date, usuario_id: str, asesor: str) -> str:
        existing = (
            self._db.table("rutero_dias")
            .select("id")
            .eq("fecha", str(fecha))
            .eq("asesor", asesor)
            .limit(1)
            .execute()
        )
        if existing.data:
            return existing.data[0]["id"]

        result = (
            self._db.table("rutero_dias")
            .insert({"fecha": str(fecha), "usuario_id": usuario_id, "asesor": asesor})
            .execute()
        )
        return result.data[0]["id"]

    async def get_rutero_dia_id(self, fecha: date, asesor: str) -> Optional[str]:
        result = (
            self._db.table("rutero_dias")
            .select("id")
            .eq("fecha", str(fecha))
            .eq("asesor", asesor)
            .limit(1)
            .execute()
        )
        return result.data[0]["id"] if result.data else None

    async def crear_llamada(self, llamada: Llamada) -> Llamada:
        payload: dict = {
            "rutero_dia_id": llamada.rutero_dia_id,
            "cliente_id": llamada.cliente_id,
            "estado": llamada.estado.value,
        }
        if llamada.posicion_cola is not None:
            payload["posicion_cola"] = llamada.posicion_cola
        # ignore_duplicates=True: si ya existe (rutero_dia_id, cliente_id),
        # NO sobreescribe estado ni ningún campo — preserva lo ya registrado.
        result = (
            self._db.table("rutero_clientes")
            .upsert(payload, on_conflict="rutero_dia_id,cliente_id", ignore_duplicates=True)
            .execute()
        )
        # upsert con ignore_duplicates no devuelve filas en conflicto;
        # recuperamos el id por búsqueda directa.
        if result.data:
            llamada.id = result.data[0]["id"]
        else:
            existing = (
                self._db.table("rutero_clientes")
                .select("id")
                .eq("rutero_dia_id", llamada.rutero_dia_id)
                .eq("cliente_id", llamada.cliente_id)
                .limit(1)
                .execute()
            )
            llamada.id = existing.data[0]["id"]
        return llamada

    async def actualizar_estado(self, rutero_cliente_id: str, estado: EstadoLlamada) -> Llamada:
        result = (
            self._db.table("rutero_clientes")
            .update({"estado": estado.value})
            .eq("id", rutero_cliente_id)
            .execute()
        )
        row = result.data[0]
        return Llamada(
            id=row["id"],
            rutero_dia_id=row["rutero_dia_id"],
            cliente_id=row["cliente_id"],
            estado=EstadoLlamada(row["estado"]),
        )

    async def get_llamadas_del_dia(self, fecha: date, asesor: str) -> List[dict]:
        rutero_dia_id = await self.get_rutero_dia_id(fecha, asesor)
        if rutero_dia_id is None:
            return []

        result = (
            self._db.table("rutero_clientes")
            .select(
                "*, "
                "clientes(id, cod_cliente, nombre, razon_social, direccion, barrio, ciudad, telefono, dias_visita)"
            )
            .eq("rutero_dia_id", rutero_dia_id)
            .order("posicion_cola", desc=False)
            .execute()
        )

        rows = result.data or []

        # Última novedad del día por rutero_cliente
        novedades_result = (
            self._db.table("novedades")
            .select("rutero_cliente_id, tipo, observacion, created_at")
            .eq("fecha", str(fecha))
            .order("created_at", desc=True)
            .execute()
        )
        novedades_por_rc: dict[str, dict] = {}
        for n in (novedades_result.data or []):
            rc_id = n["rutero_cliente_id"]
            if rc_id not in novedades_por_rc:
                novedades_por_rc[rc_id] = n

        # Notas permanentes agrupadas por cliente_id
        # Se buscan todas para evitar URLs gigantes con .in_() de cientos de UUIDs
        cliente_ids_set = {(row.get("clientes") or {}).get("id") for row in rows if row.get("clientes")}
        notas_por_cliente: dict[str, list] = {}
        notas_result = (
            self._db.table("notas_cliente")
            .select("*")
            .order("created_at", desc=False)
            .execute()
        )
        for nota in (notas_result.data or []):
            if nota["cliente_id"] in cliente_ids_set:
                notas_por_cliente.setdefault(nota["cliente_id"], []).append(nota)

        registros = []
        for row in rows:
            cliente = row.get("clientes") or {}
            rc_id = row["id"]
            cli_id = cliente.get("id")
            registros.append(
                {
                    "rutero_cliente_id": rc_id,
                    "estado": row["estado"],
                    "posicion_cola": row.get("posicion_cola"),
                    "contador_intentos": row.get("contador_intentos", 0),
                    "updated_at": row.get("updated_at"),
                    "cliente_id": cli_id,
                    "cod_cliente": cliente.get("cod_cliente"),
                    "nombre": cliente.get("nombre"),
                    "razon_social": cliente.get("razon_social"),
                    "direccion": cliente.get("direccion"),
                    "barrio": cliente.get("barrio"),
                    "ciudad": cliente.get("ciudad"),
                    "telefono": cliente.get("telefono"),
                    "dias_visita": cliente.get("dias_visita"),
                    "ultima_novedad": novedades_por_rc.get(rc_id),
                    "notas_permanentes": notas_por_cliente.get(cli_id, []),
                }
            )

        return registros

    async def crear_novedad(self, novedad: Novedad) -> Novedad:
        result = (
            self._db.table("novedades")
            .insert(
                {
                    "rutero_cliente_id": novedad.rutero_cliente_id,
                    "cliente_id": novedad.cliente_id,
                    "fecha": str(novedad.fecha),
                    "tipo": novedad.tipo.value,
                    "observacion": novedad.observacion,
                }
            )
            .execute()
        )
        row = result.data[0]
        novedad.id = row["id"]
        return novedad

    async def get_problematicos_del_dia(self, fecha: date, asesor: str) -> List[dict]:
        rutero_dia_id = await self.get_rutero_dia_id(fecha, asesor)
        if rutero_dia_id is None:
            return []

        # Se parte de TODOS los rutero_clientes del día (no solo estado
        # no_contesto/novedad): un cliente puede haber contestado y aun así
        # tener una novedad asociada, y debe salir en el reporte igual.
        result = (
            self._db.table("rutero_clientes")
            .select(
                "id, estado, "
                "clientes(nombre, razon_social, telefono)"
            )
            .eq("rutero_dia_id", rutero_dia_id)
            .execute()
        )
        rows = result.data or []
        if not rows:
            return []

        rc_ids = [row["id"] for row in rows]
        novedades_result = (
            self._db.table("novedades")
            .select("rutero_cliente_id, tipo, observacion, created_at")
            .in_("rutero_cliente_id", rc_ids)
            .order("created_at", desc=True)
            .execute()
        )
        novedad_por_rc: dict[str, dict] = {}
        for n in (novedades_result.data or []):
            rc_id = n["rutero_cliente_id"]
            if rc_id not in novedad_por_rc:
                novedad_por_rc[rc_id] = n

        registros = []
        for row in rows:
            cliente = row.get("clientes") or {}
            novedad = novedad_por_rc.get(row["id"])
            estado = row["estado"]

            if novedad is not None:
                # "Número equivocado / no existe" es el motivo por defecto
                # que pone /cola/saltar — así se distingue un salto de una
                # novedad real, sin depender del campo estado.
                if novedad["tipo"] == TipoNovedad.NUMERO_EQUIVOCADO.value:
                    estado_reporte = "Saltado"
                else:
                    estado_reporte = "Novedad"
                tipo_novedad = novedad["tipo"]
                observacion = novedad.get("observacion") or ""
            elif estado == EstadoLlamada.NO_CONTESTO.value:
                estado_reporte = "No contestó"
                tipo_novedad = ""
                observacion = "2 intentos sin respuesta"
            else:
                # Contestó sin novedad, pendiente, reagendado, etc.: no requiere acción.
                continue

            registros.append(
                {
                    "nombre": cliente.get("nombre"),
                    "razon_social": cliente.get("razon_social"),
                    "telefono": cliente.get("telefono"),
                    "estado_reporte": estado_reporte,
                    "tipo_novedad": tipo_novedad,
                    "observacion": observacion,
                }
            )

        # Agrupar por tipo de problema para que el jefe lea el reporte por bloques
        orden = {"Novedad": 0, "Saltado": 1, "No contestó": 2}
        registros.sort(key=lambda r: (orden[r["estado_reporte"]], r["nombre"] or ""))
        return registros

    async def get_historial_novedades(self, cliente_id: str) -> List[Novedad]:
        result = (
            self._db.table("novedades")
            .select("*")
            .eq("cliente_id", cliente_id)
            .order("created_at", desc=True)
            .execute()
        )
        novedades = []
        for row in (result.data or []):
            novedades.append(
                Novedad(
                    id=row["id"],
                    rutero_cliente_id=row["rutero_cliente_id"],
                    cliente_id=row["cliente_id"],
                    fecha=row["fecha"],
                    tipo=TipoNovedad(row["tipo"]),
                    observacion=row.get("observacion"),
                )
            )
        return novedades

    # ------------------------------------------------------------------
    # Cola automática
    # ------------------------------------------------------------------

    async def get_siguiente_en_cola(self, fecha: date, asesor: str) -> Optional[dict]:
        rid = await self.get_rutero_dia_id(fecha, asesor)
        if rid is None:
            return None

        ahora_iso = datetime.now(timezone.utc).isoformat()

        # 1. Reagendados cuyo tiempo ya venció
        reag = (
            self._db.table("rutero_clientes")
            .select("*, clientes(id, cod_cliente, nombre, razon_social, direccion, barrio, ciudad, telefono, dias_visita)")
            .eq("rutero_dia_id", rid)
            .eq("estado", EstadoLlamada.REAGENDADO.value)
            .lte("reagendado_para", ahora_iso)
            .order("reagendado_para", desc=False)
            .limit(1)
            .execute()
        )
        if reag.data:
            return self._enriquecer_fila(reag.data[0], viene_de_reagendamiento=True)

        # 2. Siguiente pendiente o reintento_pendiente por posicion_cola
        pend = (
            self._db.table("rutero_clientes")
            .select("*, clientes(id, cod_cliente, nombre, razon_social, direccion, barrio, ciudad, telefono, dias_visita)")
            .eq("rutero_dia_id", rid)
            .in_("estado", [EstadoLlamada.PENDIENTE.value, EstadoLlamada.REINTENTO_PENDIENTE.value])
            .order("posicion_cola", desc=False)
            .limit(1)
            .execute()
        )
        if pend.data:
            return self._enriquecer_fila(pend.data[0], viene_de_reagendamiento=False)

        return None

    def _enriquecer_fila(self, row: dict, viene_de_reagendamiento: bool) -> dict:
        cliente = row.get("clientes") or {}
        cli_id = cliente.get("id")
        notas: list = []
        if cli_id:
            n = (
                self._db.table("notas_cliente")
                .select("*")
                .eq("cliente_id", cli_id)
                .order("created_at", desc=False)
                .execute()
            )
            notas = n.data or []

        reagendado_para = row.get("reagendado_para")
        minutos_reagendado = None
        if viene_de_reagendamiento and reagendado_para:
            try:
                rp = datetime.fromisoformat(reagendado_para.replace("Z", "+00:00"))
                diff = datetime.now(timezone.utc) - rp
                minutos_reagendado = max(0, int(diff.total_seconds() / 60))
            except Exception:
                pass

        return {
            "rutero_cliente_id": row["id"],
            "estado": row["estado"],
            "posicion_cola": row.get("posicion_cola"),
            "contador_intentos": row.get("contador_intentos", 0),
            "cliente_id": cli_id,
            "cod_cliente": cliente.get("cod_cliente"),
            "nombre": cliente.get("nombre"),
            "razon_social": cliente.get("razon_social"),
            "direccion": cliente.get("direccion"),
            "barrio": cliente.get("barrio"),
            "ciudad": cliente.get("ciudad"),
            "telefono": cliente.get("telefono"),
            "dias_visita": cliente.get("dias_visita"),
            "notas_permanentes": notas,
            "viene_de_reagendamiento": viene_de_reagendamiento,
            "minutos_reagendado": minutos_reagendado,
            "reagendado_para": reagendado_para,
        }

    async def get_datos_tarjeta_cliente(self, rutero_cliente_id: str) -> dict:
        result = (
            self._db.table("rutero_clientes")
            .select(
                "id, estado, "
                "clientes(id, cod_cliente, nombre, razon_social, direccion, barrio, ciudad, telefono, dias_visita)"
            )
            .eq("id", rutero_cliente_id)
            .limit(1)
            .execute()
        )
        row = result.data[0]
        cliente = row.get("clientes") or {}
        cli_id = cliente.get("id")

        ultima_novedad = None
        nov_result = (
            self._db.table("novedades")
            .select("tipo, observacion, created_at")
            .eq("rutero_cliente_id", rutero_cliente_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if nov_result.data:
            ultima_novedad = nov_result.data[0]

        notas_result = (
            self._db.table("notas_cliente")
            .select("*")
            .eq("cliente_id", cli_id)
            .order("created_at", desc=False)
            .execute()
        ) if cli_id else None

        return {
            "rutero_cliente_id": row["id"],
            "estado": row["estado"],
            "contador_intentos": row.get("contador_intentos", 0),
            "cliente_id": cli_id,
            "cod_cliente": cliente.get("cod_cliente"),
            "nombre": cliente.get("nombre"),
            "razon_social": cliente.get("razon_social"),
            "direccion": cliente.get("direccion"),
            "barrio": cliente.get("barrio"),
            "ciudad": cliente.get("ciudad"),
            "telefono": cliente.get("telefono"),
            "dias_visita": cliente.get("dias_visita"),
            "ultima_novedad": ultima_novedad,
            "notas_permanentes": (notas_result.data or []) if notas_result else [],
        }

    async def get_cliente_de_cola(self, rutero_cliente_id: str) -> Optional[dict]:
        result = (
            self._db.table("rutero_clientes")
            .select("*, clientes(id, cod_cliente, nombre, razon_social, direccion, barrio, ciudad, telefono, dias_visita)")
            .eq("id", rutero_cliente_id)
            .limit(1)
            .execute()
        )
        if not result.data:
            return None
        row = result.data[0]
        return self._enriquecer_fila(
            row,
            viene_de_reagendamiento=(row.get("estado") == EstadoLlamada.REAGENDADO.value),
        )

    async def registrar_no_contesta_con_reintento(
        self, rutero_cliente_id: str, fecha: date
    ) -> dict:
        rc = (
            self._db.table("rutero_clientes")
            .select("contador_intentos, posicion_cola, rutero_dia_id")
            .eq("id", rutero_cliente_id)
            .limit(1)
            .execute()
        )
        row = rc.data[0]
        intentos = (row.get("contador_intentos") or 0) + 1

        if intentos >= 2:
            # Segundo fallo → no_contesto definitivo
            self._db.table("rutero_clientes").update({
                "estado": EstadoLlamada.NO_CONTESTO.value,
                "contador_intentos": intentos,
            }).eq("id", rutero_cliente_id).execute()
            return {"estado": EstadoLlamada.NO_CONTESTO.value, "contador_intentos": intentos}

        # Primer fallo → buscar posición del 4° cliente pendiente después de éste
        pos_actual = row.get("posicion_cola") or 0
        rid = row["rutero_dia_id"]

        siguientes = (
            self._db.table("rutero_clientes")
            .select("posicion_cola")
            .eq("rutero_dia_id", rid)
            .in_("estado", [EstadoLlamada.PENDIENTE.value, EstadoLlamada.REINTENTO_PENDIENTE.value])
            .gt("posicion_cola", pos_actual)
            .order("posicion_cola", desc=False)
            .limit(4)
            .execute()
        )
        filas = siguientes.data or []

        if len(filas) >= 4:
            # Insertar justo después del 4° siguiente
            nueva_pos = filas[3]["posicion_cola"] + 1
        elif filas:
            # Menos de 4 pendientes → ir al final
            nueva_pos = filas[-1]["posicion_cola"] + 1
        else:
            # No quedan pendientes con posicion_cola asignada → ir a pos_actual + 4
            nueva_pos = pos_actual + 4

        self._db.table("rutero_clientes").update({
            "estado": EstadoLlamada.REINTENTO_PENDIENTE.value,
            "contador_intentos": intentos,
            "posicion_cola": nueva_pos,
        }).eq("id", rutero_cliente_id).execute()

        return {"estado": EstadoLlamada.REINTENTO_PENDIENTE.value, "contador_intentos": intentos}

    async def reagendar(self, rutero_cliente_id: str, minutos: int, fecha: date) -> None:
        reagendado_para = (
            datetime.now(timezone.utc) + timedelta(minutes=minutos)
        ).isoformat()
        self._db.table("rutero_clientes").update({
            "estado": EstadoLlamada.REAGENDADO.value,
            "reagendado_para": reagendado_para,
        }).eq("id", rutero_cliente_id).execute()

    async def get_reagendados_no_vencidos(self, fecha: date, asesor: str) -> List[dict]:
        rutero_dia_id = await self.get_rutero_dia_id(fecha, asesor)
        if rutero_dia_id is None:
            return []

        ahora_iso = datetime.now(timezone.utc).isoformat()
        result = (
            self._db.table("rutero_clientes")
            .select("id, reagendado_para, clientes(nombre)")
            .eq("rutero_dia_id", rutero_dia_id)
            .eq("estado", EstadoLlamada.REAGENDADO.value)
            .gt("reagendado_para", ahora_iso)
            .order("reagendado_para", desc=False)
            .execute()
        )
        return [
            {
                "rutero_cliente_id": row["id"],
                "nombre": (row.get("clientes") or {}).get("nombre"),
                "reagendado_para": row["reagendado_para"],
            }
            for row in (result.data or [])
        ]

    # ------------------------------------------------------------------
    # Integración con el teléfono (WebSocket)
    # ------------------------------------------------------------------

    async def get_datos_para_llamar(self, rutero_cliente_id: str) -> dict:
        result = (
            self._db.table("rutero_clientes")
            .select("id, clientes(nombre, telefono)")
            .eq("id", rutero_cliente_id)
            .limit(1)
            .execute()
        )
        if not result.data:
            raise ValueError(f"rutero_cliente '{rutero_cliente_id}' no existe")
        cliente = result.data[0].get("clientes") or {}
        return {
            "telefono": cliente.get("telefono"),
            "nombre": cliente.get("nombre"),
        }

    async def asociar_llamada_telefono(self, rutero_cliente_id: str, llamada_id: str) -> None:
        self._db.table("rutero_clientes").update({
            "llamada_id": llamada_id,
        }).eq("id", rutero_cliente_id).execute()

    async def guardar_duracion_llamada(self, llamada_id: str, duracion_seg: int) -> None:
        self._db.table("rutero_clientes").update({
            "duracion_seg": duracion_seg,
        }).eq("llamada_id", llamada_id).execute()

    async def contar_rutero_dia(self, fecha: date, asesor: str) -> dict:
        rutero_dia_id = await self.get_rutero_dia_id(fecha, asesor)
        if rutero_dia_id is None:
            return {"total": 0, "ya_llamados": 0}

        result = (
            self._db.table("rutero_clientes")
            .select("estado")
            .eq("rutero_dia_id", rutero_dia_id)
            .execute()
        )
        rows = result.data or []
        ya_llamados = sum(
            1 for r in rows
            if r["estado"] in (EstadoLlamada.CONTESTO.value, EstadoLlamada.NO_CONTESTO.value)
        )
        return {"total": len(rows), "ya_llamados": ya_llamados}

    async def eliminar_rutero_dia(self, fecha: date, asesor: str) -> bool:
        rutero_dia_id = await self.get_rutero_dia_id(fecha, asesor)
        if rutero_dia_id is None:
            return False
        self._db.table("rutero_dias").delete().eq("id", rutero_dia_id).execute()
        return True
