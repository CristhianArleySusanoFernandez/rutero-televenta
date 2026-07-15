from datetime import date
from typing import Optional

from pydantic import BaseModel

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from src.api.dependencies import (
    get_llamada_repo,
    get_obtener_cliente_especifico,
    get_obtener_historial,
    get_obtener_siguiente_cliente,
    get_ordenar_llamada_cliente,
    get_registrar_no_contesta,
    get_telefono_gateway,
)
from src.api.templates_config import templates
from src.config import settings
from src.domain.value_objects.estado_llamada import EstadoLlamada
from src.application.use_cases.obtener_cliente_especifico import ObtenerClienteEspecifico
from src.application.use_cases.obtener_historial import ObtenerHistorial
from src.application.use_cases.obtener_siguiente_cliente import ObtenerSiguienteCliente
from src.application.use_cases.ordenar_llamada_cliente import OrdenarLlamadaCliente
from src.application.use_cases.registrar_no_contesta import RegistrarNoContesta
from src.infrastructure.adapters.supabase_llamada_repository import SupabaseLlamadaRepository
from src.infrastructure.adapters.websocket_telefono_gateway import WebSocketTelefonoGateway

router = APIRouter(prefix="/cola", tags=["cola"])


class RuteroClienteBody(BaseModel):
    rutero_cliente_id: str


class SaltarBody(BaseModel):
    rutero_cliente_id: str
    cliente_id: str
    motivo: str = "Número equivocado / no existe"


class ReagendarBody(BaseModel):
    rutero_cliente_id: str
    minutos: int


@router.get("/siguiente")
async def siguiente_cliente(
    fecha: Optional[date] = Query(None),
    uc: ObtenerSiguienteCliente = Depends(get_obtener_siguiente_cliente),
):
    fecha_efectiva = fecha or date.today()
    resultado = await uc.execute(fecha_efectiva)
    return JSONResponse(resultado)


@router.get("/vista-enfocada", response_class=HTMLResponse)
async def vista_enfocada(
    request: Request,
    fecha: Optional[date] = Query(None),
    rc: Optional[str] = Query(None),
    uc: ObtenerSiguienteCliente = Depends(get_obtener_siguiente_cliente),
    uc_especifico: ObtenerClienteEspecifico = Depends(get_obtener_cliente_especifico),
    uc_historial: ObtenerHistorial = Depends(get_obtener_historial),
):
    fecha_efectiva = fecha or date.today()

    async def _render_cliente(cliente: dict):
        # Historial abierto por defecto en la vista enfocada
        historial = []
        if cliente.get("cliente_id"):
            historial = await uc_historial.execute(cliente["cliente_id"])
        return templates.TemplateResponse(
            request,
            "partials/vista_enfocada.html",
            {"cliente": cliente, "historial": historial},
        )

    # 'Atender ahora': cliente específico fuera del orden normal.
    # Si ya no es atendible (datos viejos), cae al flujo normal sin error.
    if rc:
        cliente = await uc_especifico.execute(rc)
        if cliente is not None:
            return await _render_cliente(cliente)

    resultado = await uc.execute(fecha_efectiva)

    if resultado["situacion"] == "cliente":
        return await _render_cliente(resultado["cliente"])

    if resultado["situacion"] == "esperando":
        return templates.TemplateResponse(
            request,
            "partials/espera_reagendados.html",
            {"total": resultado["total"], "reagendados": resultado["reagendados"]},
        )

    # situacion == "terminado": nadie pendiente, ni reintento, ni reagendado
    return HTMLResponse("""
    <div id="vista-enfocada" class="max-w-lg mx-auto text-center py-20 space-y-4">
        <p class="text-6xl">🎉</p>
        <h2 class="text-2xl font-bold text-marca">¡Terminaste por hoy!</h2>
        <p class="text-gray-500">No quedan clientes pendientes en la cola.</p>
    </div>
    """)


@router.post("/saltar")
async def saltar_cliente(
    body: SaltarBody,
    repo: SupabaseLlamadaRepository = Depends(get_llamada_repo),
):
    """
    Salta un cliente de la cola sin reinsertarlo:
    1. Registra novedad automática con el motivo indicado.
    2. Marca estado = no_contesto directamente (sin lógica de reintentos).
    """
    from src.domain.entities.novedad import Novedad
    from src.domain.value_objects.tipo_novedad import TipoNovedad

    # Intentar mapear el motivo a un TipoNovedad; si no coincide, usar OTRO
    try:
        tipo = TipoNovedad(body.motivo)
    except ValueError:
        tipo = TipoNovedad.OTRO

    novedad = Novedad(
        rutero_cliente_id=body.rutero_cliente_id,
        cliente_id=body.cliente_id,
        fecha=date.today(),
        tipo=tipo,
        observacion=body.motivo if tipo == TipoNovedad.OTRO else None,
    )
    await repo.crear_novedad(novedad)
    await repo.actualizar_estado(body.rutero_cliente_id, EstadoLlamada.NO_CONTESTO)
    return JSONResponse({"ok": True})


class LlamarColaBody(BaseModel):
    rutero_cliente_id: str


def _resolver_telefono_id(gateway: WebSocketTelefonoGateway) -> tuple[Optional[str], Optional[dict]]:
    """
    Regla híbrida de selección del teléfono (Opción A: un teléfono por PC):
      1. TELEFONO_ID en .env → usar ese.
      2. Sin config y exactamente 1 conectado → usar el único.
      3. Sin config y 0 conectados → error.
      4. Sin config y 2+ conectados → error (pedir config explícita).

    Devuelve (telefono_id, None) si resuelve, o (None, {error, status}) si no.
    """
    if settings.telefono_id:
        sesion = gateway.get_sesion(settings.telefono_id)
        if sesion is None:
            return None, {
                "error": (
                    f"El teléfono configurado '{settings.telefono_id}' no está conectado. "
                    "Verifica que la app esté abierta y en la misma red WiFi."
                ),
                "status": 404,
            }
        return settings.telefono_id, None

    sesiones = gateway.listar_sesiones()
    if not sesiones:
        return None, {
            "error": (
                "No hay ningún teléfono conectado. "
                "Abre la app en el teléfono y verifica que esté en la misma red WiFi."
            ),
            "status": 404,
        }
    if len(sesiones) > 1:
        ids = ", ".join(s.telefono_id for s in sesiones)
        return None, {
            "error": (
                f"Hay varios teléfonos conectados ({ids}). "
                "Configura TELEFONO_ID en el archivo .env para elegir cuál usar."
            ),
            "status": 409,
        }
    return sesiones[0].telefono_id, None


@router.post("/llamar")
async def llamar_cliente_actual(
    body: LlamarColaBody,
    uc: OrdenarLlamadaCliente = Depends(get_ordenar_llamada_cliente),
    gateway: WebSocketTelefonoGateway = Depends(get_telefono_gateway),
):
    """
    El asesor confirma la llamada al cliente actual de la cola.
    Resuelve qué teléfono usar, ordena marcar y asocia el llamada_id
    al rutero_cliente para correlacionar la duración cuando llegue el IDLE.
    """
    telefono_id, err = _resolver_telefono_id(gateway)
    if err:
        return JSONResponse({"error": err["error"]}, status_code=err["status"])

    try:
        resultado = await uc.execute(body.rutero_cliente_id, telefono_id)
    except ValueError as e:
        # Teléfono del cliente inválido o rutero_cliente inexistente
        return JSONResponse({"error": str(e)}, status_code=400)
    except RuntimeError as e:
        # Teléfono desconectado u ocupado (en llamada / no disponible)
        return JSONResponse({"error": str(e)}, status_code=409)

    return JSONResponse({
        "ok": True,
        "llamada_id": resultado["llamada_id"],
        "numero": resultado["numero"],
        "telefono_id": telefono_id,
    })


@router.post("/no-contesto")
async def no_contesto_con_reintento(
    body: RuteroClienteBody,
    uc: RegistrarNoContesta = Depends(get_registrar_no_contesta),
):
    resultado = await uc.execute(body.rutero_cliente_id, date.today())
    return JSONResponse(resultado)


@router.post("/reagendar")
async def reagendar(
    body: ReagendarBody,
    repo: SupabaseLlamadaRepository = Depends(get_llamada_repo),
):
    from datetime import date
    await repo.reagendar(body.rutero_cliente_id, body.minutos, date.today())
    return JSONResponse({"ok": True})
