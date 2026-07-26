import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Awaitable, Callable, Optional

from fastapi import WebSocket, WebSocketDisconnect

from src.domain.entities.sesion_telefono import SesionTelefono
from src.domain.ports.telefono_gateway import TelefonoGateway

log = logging.getLogger(__name__)

# Según contrato §3: timeout = 90s (3 heartbeats perdidos de 30s cada uno)
_TIMEOUT_SIN_MENSAJE = 90
_INTERVALO_WATCHDOG  = 30   # revisar cada 30s


def _ts_ahora() -> str:
    """Marca de tiempo UTC en ISO 8601 con sufijo Z, tal como exige el contrato."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


class WebSocketTelefonoGateway(TelefonoGateway):
    """
    Implementación del puerto TelefonoGateway sobre WebSocket.

    Una instancia de esta clase vive como singleton en el proceso FastAPI
    (se crea en dependencies.py y se reutiliza en cada request).

    Responsabilidades:
      - Mantener el mapa telefono_id → WebSocket (ConnectionManager)
      - Mantener el mapa telefono_id → SesionTelefono (estado en memoria)
      - Despachar mensajes entrantes del teléfono según contrato §4
      - Enviar mensajes 'llamar' y 'colgar' según contrato §5
      - Watchdog: desconectar sesiones sin mensaje en > 90s
    """

    def __init__(self) -> None:
        # telefono_id → WebSocket activo
        self._conexiones: dict[str, WebSocket] = {}
        # telefono_id → SesionTelefono
        self._sesiones: dict[str, SesionTelefono] = {}
        # tarea asyncio del watchdog
        self._tarea_watchdog: Optional[asyncio.Task] = None
        # Hook opcional: se invoca al recibir IDLE con (llamada_id, duracion_seg).
        # Lo cablea la capa de composición (dependencies.py); el adapter no sabe
        # qué hay detrás (caso de uso, Supabase, etc.).
        self.on_llamada_finalizada: Optional[Callable[[str, int], Awaitable[None]]] = None

    # ─────────────────────────────────────────────
    # Ciclo de vida de la conexión
    # ─────────────────────────────────────────────

    async def conectar(self, websocket: WebSocket) -> None:
        """
        Acepta la conexión WebSocket y entra en el loop de lectura de mensajes.
        Bloquea hasta que el teléfono se desconecte.
        """
        await websocket.accept()
        telefono_id: Optional[str] = None

        try:
            async for raw in websocket.iter_text():
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    log.warning("WS: mensaje no es JSON válido — ignorado: %s", raw[:120])
                    continue

                tipo = msg.get("tipo")
                if not tipo:
                    log.warning("WS: mensaje sin campo 'tipo' — ignorado")
                    continue

                # El primer mensaje DEBE ser 'registro' (contrato §3 punto 2)
                if telefono_id is None and tipo != "registro":
                    log.warning(
                        "WS: primer mensaje no es 'registro' (es '%s') — ignorado hasta recibir registro",
                        tipo,
                    )
                    continue

                telefono_id = await self._despachar(msg, websocket, telefono_id)

        except WebSocketDisconnect:
            log.info("WS: desconexión de '%s'", telefono_id or "<sin registrar>")
        except Exception:
            log.exception("WS: error inesperado en conexión de '%s'", telefono_id)
        finally:
            if telefono_id:
                self._limpiar_sesion(telefono_id)

    def _limpiar_sesion(self, telefono_id: str) -> None:
        self._conexiones.pop(telefono_id, None)
        sesion = self._sesiones.pop(telefono_id, None)
        if sesion:
            sesion.conectado = False
        log.info("WS: sesión limpiada para '%s'", telefono_id)

    # ─────────────────────────────────────────────
    # Despacho de mensajes entrantes (contrato §4)
    # ─────────────────────────────────────────────

    async def _despachar(
        self,
        msg: dict,
        websocket: WebSocket,
        telefono_id_actual: Optional[str],
    ) -> str:
        """Enruta el mensaje al handler correcto. Devuelve el telefono_id efectivo."""
        tipo = msg.get("tipo")

        if tipo == "registro":
            return await self._handle_registro(msg, websocket)

        tid = msg.get("telefono_id", telefono_id_actual)

        if tipo == "disponible":
            self._handle_disponible(tid)
        elif tipo == "estado_llamada":
            self._handle_estado_llamada(msg, tid)
        elif tipo == "salud":
            self._handle_salud(msg, tid)
        else:
            # Contrato §1: mensajes desconocidos se ignoran sin cerrar la conexión
            log.debug("WS: tipo desconocido '%s' de '%s' — ignorado", tipo, tid)

        return telefono_id_actual or tid

    async def _handle_registro(self, msg: dict, websocket: WebSocket) -> str:
        """Contrato §4.1 — primer mensaje obligatorio al conectar."""
        tid = msg.get("telefono_id", "")
        if not tid:
            log.warning("WS: 'registro' sin telefono_id — ignorado")
            return ""

        # Si ya había sesión para este id, reemplazar (contrato §3 punto: sesión anterior se descarta)
        if tid in self._conexiones:
            log.info("WS: reemplazando sesión existente de '%s'", tid)
            self._limpiar_sesion(tid)

        self._conexiones[tid] = websocket
        self._sesiones[tid] = SesionTelefono(
            telefono_id=tid,
            modelo=msg.get("modelo"),
            android_version=msg.get("android_version"),
            app_version=msg.get("app_version"),
            bateria=msg.get("bateria"),
        )
        log.info(
            "WS: teléfono registrado — id='%s' modelo='%s' android='%s' bateria=%s%%",
            tid,
            msg.get("modelo"),
            msg.get("android_version"),
            msg.get("bateria"),
        )
        # Arrancar watchdog la primera vez que hay un teléfono
        self._asegurar_watchdog()
        return tid

    def _handle_disponible(self, telefono_id: str) -> None:
        """Contrato §4.2 — teléfono libre para recibir órdenes."""
        sesion = self._sesiones.get(telefono_id)
        if sesion:
            sesion.marcar_disponible()
            log.info("WS: '%s' marcado como disponible", telefono_id)

    def _handle_estado_llamada(self, msg: dict, telefono_id: str) -> None:
        """Contrato §4.3 — OFFHOOK o IDLE."""
        sesion = self._sesiones.get(telefono_id)
        if not sesion:
            return

        estado      = msg.get("estado")
        llamada_id  = msg.get("llamada_id")
        duracion    = msg.get("duracion_seg")

        if estado == "OFFHOOK":
            sesion.iniciar_llamada(llamada_id)
            log.info("WS: '%s' OFFHOOK — llamada_id=%s", telefono_id, llamada_id)
        elif estado == "IDLE":
            sesion.finalizar_llamada()
            log.info(
                "WS: '%s' IDLE — llamada_id=%s duración=%ss",
                telefono_id, llamada_id, duracion,
            )
            if self.on_llamada_finalizada and llamada_id and duracion is not None:
                # En tarea aparte: persistir no debe bloquear el loop de lectura
                # ni tumbar la conexión si falla.
                asyncio.create_task(self.on_llamada_finalizada(llamada_id, duracion))
        else:
            log.debug("WS: estado_llamada desconocido '%s' de '%s'", estado, telefono_id)

    def _handle_salud(self, msg: dict, telefono_id: str) -> None:
        """Contrato §4.4 — heartbeat cada 30s."""
        sesion = self._sesiones.get(telefono_id)
        if not sesion:
            return
        sesion.actualizar_salud(
            bateria=msg.get("bateria", sesion.bateria or 0),
            cargando=msg.get("cargando", False),
            en_llamada=msg.get("en_llamada", False),
        )
        log.debug(
            "WS: salud de '%s' — bateria=%s%% cargando=%s en_llamada=%s",
            telefono_id,
            msg.get("bateria"),
            msg.get("cargando"),
            msg.get("en_llamada"),
        )

    # ─────────────────────────────────────────────
    # Mensajes salientes: servidor → teléfono (contrato §5)
    # ─────────────────────────────────────────────

    async def ordenar_llamada(
        self,
        telefono_id: str,
        llamada_id: str,
        numero: str,
        nombre_contacto: Optional[str] = None,
    ) -> None:
        """Contrato §5.1 — envía 'llamar' al teléfono."""
        sesion = self._sesiones.get(telefono_id)
        if not sesion or not sesion.conectado:
            raise RuntimeError(f"Teléfono '{telefono_id}' no está conectado")
        if not sesion.disponible:
            raise RuntimeError(f"Teléfono '{telefono_id}' no está disponible (en_llamada={sesion.en_llamada})")

        payload = {
            "tipo": "llamar",
            "telefono_id": telefono_id,
            "ts": _ts_ahora(),
            "llamada_id": llamada_id,
            "numero": numero,
            "nombre_contacto": nombre_contacto,
        }
        await self._enviar(telefono_id, payload)
        log.info("WS: 'llamar' enviado a '%s' — numero=%s llamada_id=%s", telefono_id, numero, llamada_id)

    async def ordenar_colgar(self, telefono_id: str, llamada_id: str) -> None:
        """Contrato §5.2 — envía 'colgar' al teléfono."""
        payload = {
            "tipo": "colgar",
            "telefono_id": telefono_id,
            "ts": _ts_ahora(),
            "llamada_id": llamada_id,
        }
        await self._enviar(telefono_id, payload)
        log.info("WS: 'colgar' enviado a '%s' — llamada_id=%s", telefono_id, llamada_id)

    async def _enviar(self, telefono_id: str, payload: dict) -> None:
        ws = self._conexiones.get(telefono_id)
        if not ws:
            raise RuntimeError(f"Sin conexión WebSocket activa para '{telefono_id}'")
        await ws.send_text(json.dumps(payload, ensure_ascii=False))

    # ─────────────────────────────────────────────
    # Consulta de estado (implementación del puerto)
    # ─────────────────────────────────────────────

    def get_sesion(self, telefono_id: str) -> Optional[SesionTelefono]:
        return self._sesiones.get(telefono_id)

    def listar_sesiones(self) -> list[SesionTelefono]:
        return list(self._sesiones.values())

    # ─────────────────────────────────────────────
    # Watchdog de heartbeat (contrato §3 punto 5)
    # ─────────────────────────────────────────────

    def _asegurar_watchdog(self) -> None:
        """Arranca el watchdog solo si no hay una tarea corriendo."""
        if self._tarea_watchdog is None or self._tarea_watchdog.done():
            self._tarea_watchdog = asyncio.create_task(self._watchdog_loop())

    async def _watchdog_loop(self) -> None:
        """
        Cada 30s revisa todos los teléfonos.
        Si alguno lleva > 90s sin mensaje, lo considera desconectado
        y limpia su sesión (contrato §3 punto 5).
        """
        log.info("WS: watchdog iniciado (intervalo=%ds timeout=%ds)", _INTERVALO_WATCHDOG, _TIMEOUT_SIN_MENSAJE)
        while self._sesiones:
            await asyncio.sleep(_INTERVALO_WATCHDOG)
            caducos = [
                tid for tid, s in list(self._sesiones.items())
                if s.segundos_sin_mensaje() > _TIMEOUT_SIN_MENSAJE
            ]
            for tid in caducos:
                log.warning(
                    "WS: watchdog — '%s' sin mensaje en >%ds, limpiando sesión",
                    tid, _TIMEOUT_SIN_MENSAJE,
                )
                self._limpiar_sesion(tid)
        log.info("WS: watchdog detenido (sin sesiones activas)")
