from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from src.api.dependencies import (
    get_obtener_historial,
    get_registrar_llamada,
    get_registrar_novedad,
)
from src.application.use_cases.obtener_historial import ObtenerHistorial
from src.application.use_cases.registrar_llamada import RegistrarLlamada
from src.application.use_cases.registrar_novedad import RegistrarNovedad
from src.domain.value_objects.estado_llamada import EstadoLlamada
from src.domain.value_objects.tipo_novedad import TipoNovedad

router = APIRouter(prefix="/llamadas", tags=["llamadas"])
from src.api.templates_config import templates


class EstadoBody(BaseModel):
    estado: EstadoLlamada


class NovedadBody(BaseModel):
    cliente_id: str
    tipo: TipoNovedad
    observacion: str | None = None
    fecha: date | None = None


@router.patch("/{rutero_cliente_id}/estado", response_class=HTMLResponse)
async def actualizar_estado(
    request: Request,
    rutero_cliente_id: str,
    body: EstadoBody,
    uc: RegistrarLlamada = Depends(get_registrar_llamada),
):
    try:
        await uc.execute(rutero_cliente_id, body.estado)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    cliente_data = await _get_cliente_data(rutero_cliente_id)
    return templates.TemplateResponse(
        request,
        "partials/cliente_card.html",
        {"cliente": cliente_data},
    )


@router.post("/{rutero_cliente_id}/novedad", response_class=HTMLResponse)
async def registrar_novedad(
    request: Request,
    rutero_cliente_id: str,
    body: NovedadBody,
    uc: RegistrarNovedad = Depends(get_registrar_novedad),
):
    try:
        await uc.execute(
            rutero_cliente_id=rutero_cliente_id,
            cliente_id=body.cliente_id,
            tipo=body.tipo,
            observacion=body.observacion,
            # Debe quedar con la fecha del rutero que se está trabajando, no la
            # fecha calendario real — si no, un rutero de un día distinto al
            # actual guarda la novedad bajo "hoy" y el reporte de ese día sale
            # vacío aunque la novedad sí se haya registrado.
            fecha=body.fecha or date.today(),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    cliente_data = await _get_cliente_data(rutero_cliente_id)
    return templates.TemplateResponse(
        request,
        "partials/cliente_card.html",
        {"cliente": cliente_data},
    )


@router.get("/{rutero_cliente_id}/novedad-form", response_class=HTMLResponse)
async def novedad_form(
    request: Request,
    rutero_cliente_id: str,
    cliente_id: str,
):
    tipos = [t.value for t in TipoNovedad]
    return templates.TemplateResponse(
        request,
        "partials/novedad_form.html",
        {
            "rutero_cliente_id": rutero_cliente_id,
            "cliente_id": cliente_id,
            "tipos": tipos,
        },
    )


@router.get("/{cliente_id}/historial", response_class=HTMLResponse)
async def historial(
    request: Request,
    cliente_id: str,
    uc: ObtenerHistorial = Depends(get_obtener_historial),
):
    novedades = await uc.execute(cliente_id)
    return templates.TemplateResponse(
        request,
        "partials/historial.html",
        {"novedades": novedades},
    )


async def _get_cliente_data(rutero_cliente_id: str) -> dict:
    from src.infrastructure.supabase_client import get_supabase
    db = get_supabase()
    result = (
        db.table("rutero_clientes")
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
        db.table("novedades")
        .select("tipo, observacion, created_at")
        .eq("rutero_cliente_id", rutero_cliente_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if nov_result.data:
        ultima_novedad = nov_result.data[0]

    notas_result = (
        db.table("notas_cliente")
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
