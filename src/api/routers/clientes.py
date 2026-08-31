from datetime import time

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from src.api.dependencies import (
    get_anular_novedad,
    get_asesor_actual,
    get_buscar_clientes,
    get_cliente_repo,
    get_editar_cliente,
    get_editar_franja_horaria,
    get_obtener_historial_cliente_asesor,
)
from src.api.templates_config import templates
from src.application.use_cases.anular_novedad import (
    AnularNovedad,
    NovedadAjena,
    NovedadNoEncontrada,
    NovedadYaAnulada,
)
from src.application.use_cases.buscar_clientes import BuscarClientes, MIN_CARACTERES
from src.application.use_cases.editar_cliente import EditarCliente
from src.application.use_cases.editar_franja_horaria import EditarFranjaHoraria
from src.application.use_cases.obtener_historial_cliente_asesor import ObtenerHistorialClienteAsesor
from src.infrastructure.adapters.supabase_cliente_repository import SupabaseClienteRepository

router = APIRouter(prefix="/clientes", tags=["clientes"])


class AnularNovedadBody(BaseModel):
    motivo: str


class EditarClienteBody(BaseModel):
    nombre: str
    razon_social: str | None = None
    direccion: str | None = None
    barrio: str | None = None
    ciudad: str | None = None
    telefono: str | None = None
    documento: str | None = None


class FranjaHorariaBody(BaseModel):
    franja_desde: time | None = None
    franja_hasta: time | None = None


@router.get("/buscador", response_class=HTMLResponse)
async def pagina_buscador(request: Request):
    return templates.TemplateResponse(request, "buscador_clientes.html", {})


@router.get("/buscar", response_class=HTMLResponse)
async def buscar_clientes(
    request: Request,
    q: str = Query(""),
    uc: BuscarClientes = Depends(get_buscar_clientes),
):
    termino = q.strip()
    if termino and len(termino) < MIN_CARACTERES:
        return templates.TemplateResponse(
            request,
            "partials/resultados_clientes.html",
            {"clientes": [], "termino": termino, "muy_corto": True},
        )

    clientes = await uc.execute(termino) if termino else []
    return templates.TemplateResponse(
        request,
        "partials/resultados_clientes.html",
        {"clientes": clientes, "termino": termino, "muy_corto": False},
    )


@router.get("/{cliente_id}/historial", response_class=HTMLResponse)
async def historial_cliente(
    request: Request,
    cliente_id: str,
    asesor: str = Depends(get_asesor_actual),
    uc: ObtenerHistorialClienteAsesor = Depends(get_obtener_historial_cliente_asesor),
):
    novedades = await uc.execute(cliente_id, asesor)
    return templates.TemplateResponse(
        request,
        "partials/historial_cliente_novedades.html",
        {"novedades": novedades, "cliente_id": cliente_id},
    )


@router.get("/{cliente_id}/ficha", response_class=HTMLResponse)
async def ficha_cliente(
    request: Request,
    cliente_id: str,
    repo: SupabaseClienteRepository = Depends(get_cliente_repo),
):
    cliente = await repo.get_by_id(cliente_id)
    return templates.TemplateResponse(
        request,
        "partials/ficha_cliente.html",
        {"cliente": cliente, "cliente_id": cliente_id},
    )


@router.post("/{cliente_id}", response_class=HTMLResponse)
async def editar_cliente(
    request: Request,
    cliente_id: str,
    body: EditarClienteBody,
    uc: EditarCliente = Depends(get_editar_cliente),
    repo: SupabaseClienteRepository = Depends(get_cliente_repo),
):
    error = None
    guardado = False
    try:
        await uc.execute(cliente_id, body.model_dump())
        guardado = True
    except ValueError as e:
        error = str(e)

    cliente = await repo.get_by_id(cliente_id)
    return templates.TemplateResponse(
        request,
        "partials/ficha_cliente.html",
        {"cliente": cliente, "cliente_id": cliente_id, "error": error, "guardado": guardado},
    )


@router.post("/{cliente_id}/franja")
async def guardar_franja_horaria(
    cliente_id: str,
    body: FranjaHorariaBody,
    uc: EditarFranjaHoraria = Depends(get_editar_franja_horaria),
):
    """
    Guarda o borra (ambas None) la franja horaria preferida del cliente.
    No toca ningún estado de cola ni registra novedades — es información
    permanente del cliente para las próximas veces que aparezca.
    """
    try:
        await uc.execute(cliente_id, body.franja_desde, body.franja_hasta)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


@router.post("/novedades/{novedad_id}/anular", response_class=HTMLResponse)
async def anular_novedad(
    request: Request,
    novedad_id: str,
    body: AnularNovedadBody,
    cliente_id: str = Query(...),
    asesor: str = Depends(get_asesor_actual),
    uc: AnularNovedad = Depends(get_anular_novedad),
    uc_historial: ObtenerHistorialClienteAsesor = Depends(get_obtener_historial_cliente_asesor),
):
    error = None
    try:
        await uc.execute(novedad_id, asesor, body.motivo)
    except (NovedadNoEncontrada, NovedadAjena) as e:
        error = str(e)
    except NovedadYaAnulada as e:
        error = str(e)
    except ValueError as e:
        error = str(e)

    novedades = await uc_historial.execute(cliente_id, asesor)
    return templates.TemplateResponse(
        request,
        "partials/historial_cliente_novedades.html",
        {"novedades": novedades, "cliente_id": cliente_id, "error": error},
    )
