from datetime import date
from typing import Optional

from pydantic import BaseModel

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from src.api.dependencies import (
    get_asesor_actual,
    get_asesor_repo,
    get_llamada_repo,
    get_obtener_cliente_especifico,
    get_obtener_historial,
    get_obtener_siguiente_cliente,
    get_ordenar_llamada_cliente,
    get_registrar_no_contesta,
    get_telefono_gateway,
)
from src.api.templates_config import templates
from src.domain.ports.asesor_repository import AsesorRepository
from src.domain.servicios.fecha_colombia import hoy_colombia
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
    fecha: Optional[date] = None


class ReagendarBody(BaseModel):
    rutero_cliente_id: str
    minutos: int


@router.get("/vista-enfocada", response_class=HTMLResponse)
async def vista_enfocada(
    request: Request,
    fecha: Optional[date] = Query(None),
    rc: Optional[str] = Query(None),
    asesor: str = Depends(get_asesor_actual),
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

    resultado = await uc.execute(fecha_efectiva, asesor)

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
    asesor: str = Depends(get_asesor_actual),
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
        # Debe quedar con la fecha del rutero que se está trabajando, no la
        # fecha calendario real (mismo caso que /llamadas/.../novedad).
        fecha=body.fecha or hoy_colombia(),
        tipo=tipo,
        observacion=body.motivo if tipo == TipoNovedad.OTRO else None,
        asesor=asesor,
    )
    await repo.crear_novedad(novedad)
    await repo.actualizar_estado(body.rutero_cliente_id, EstadoLlamada.NO_CONTESTO)
    return JSONResponse({"ok": True})


class LlamarColaBody(BaseModel):
    rutero_cliente_id: str


async def _resolver_telefono_id(
    gateway: WebSocketTelefonoGateway, asesor: str, asesor_repo: AsesorRepository
) -> tuple[Optional[str], Optional[dict]]:
    """
    El teléfono a usar es el vinculado al asesor de la sesión actual
    (tabla 'asesores'), no cualquiera que esté conectado — varias
    asesoras pueden tener el teléfono abierto al mismo tiempo.

    Devuelve (telefono_id, None) si resuelve, o (None, {error, status}) si no.
    """
    telefono_id = await asesor_repo.get_telefono_id(asesor)
    if not telefono_id:
        return None, {
            "error": (
                f"'{asesor}' no tiene un teléfono configurado. "
                "Ve a 'Cambiar asesor' y configura tu teléfono."
            ),
            "status": 400,
        }

    sesion = gateway.get_sesion(telefono_id)
    if sesion is None:
        return None, {
            "error": (
                f"Tu teléfono ('{telefono_id}') no está conectado. "
                "Verifica que la app esté abierta y en la misma red/internet."
            ),
            "status": 404,
        }
    return telefono_id, None


@router.post("/llamar")
async def llamar_cliente_actual(
    body: LlamarColaBody,
    asesor: str = Depends(get_asesor_actual),
    uc: OrdenarLlamadaCliente = Depends(get_ordenar_llamada_cliente),
    gateway: WebSocketTelefonoGateway = Depends(get_telefono_gateway),
    asesor_repo: AsesorRepository = Depends(get_asesor_repo),
):
    """
    El asesor confirma la llamada al cliente actual de la cola.
    Resuelve qué teléfono usar, ordena marcar y asocia el llamada_id
    al rutero_cliente para correlacionar la duración cuando llegue el IDLE.
    """
    telefono_id, err = await _resolver_telefono_id(gateway, asesor, asesor_repo)
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
