from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from src.api.dependencies import (
    ASESOR_COOKIE,
    get_asesor_actual,
    get_asesor_repo,
    get_listar_asesores,
    get_seleccionar_asesor,
)
from src.api.templates_config import templates
from src.application.use_cases.listar_asesores import ListarAsesores
from src.application.use_cases.seleccionar_asesor import SeleccionarAsesor
from src.domain.ports.asesor_repository import AsesorRepository

router = APIRouter(prefix="/asesor", tags=["asesor"])


@router.get("/seleccionar", response_class=HTMLResponse)
async def pantalla_seleccion(
    request: Request,
    uc: ListarAsesores = Depends(get_listar_asesores),
):
    nombres = await uc.execute()
    return templates.TemplateResponse(
        request,
        "seleccionar_asesor.html",
        {"nombres": nombres},
    )


@router.post("/seleccionar")
async def seleccionar_asesor(
    nombre: str = Form(...),
    uc: SeleccionarAsesor = Depends(get_seleccionar_asesor),
):
    try:
        await uc.execute(nombre)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    respuesta = RedirectResponse("/", status_code=303)
    respuesta.set_cookie(
        ASESOR_COOKIE, nombre.strip(), max_age=60 * 60 * 24 * 365, httponly=True
    )
    return respuesta


@router.post("/salir")
async def salir():
    """'Cambiar asesor': borra la cookie y vuelve a la pantalla de selección."""
    respuesta = RedirectResponse("/asesor/seleccionar", status_code=303)
    respuesta.delete_cookie(ASESOR_COOKIE)
    return respuesta


@router.get("/telefono", response_class=HTMLResponse)
async def pantalla_telefono(
    request: Request,
    asesor: str = Depends(get_asesor_actual),
    asesor_repo: AsesorRepository = Depends(get_asesor_repo),
):
    telefono_actual = await asesor_repo.get_telefono_id(asesor)
    return templates.TemplateResponse(
        request,
        "configurar_telefono.html",
        {"asesor": asesor, "telefono_actual": telefono_actual},
    )


@router.post("/telefono")
async def guardar_telefono(
    telefono_id: str = Form(...),
    asesor: str = Depends(get_asesor_actual),
    asesor_repo: AsesorRepository = Depends(get_asesor_repo),
):
    await asesor_repo.set_telefono_id(asesor, telefono_id.strip())
    return RedirectResponse("/", status_code=303)


@router.get("/codigo", response_class=HTMLResponse)
async def pantalla_codigo_asesor(
    request: Request,
    asesor: str = Depends(get_asesor_actual),
    asesor_repo: AsesorRepository = Depends(get_asesor_repo),
):
    codigo_actual = await asesor_repo.get_codigo_asesor(asesor)
    return templates.TemplateResponse(
        request,
        "configurar_codigo_asesor.html",
        {"asesor": asesor, "codigo_actual": codigo_actual},
    )


@router.post("/codigo")
async def guardar_codigo_asesor(
    codigo_asesor: str = Form(...),
    asesor: str = Depends(get_asesor_actual),
    asesor_repo: AsesorRepository = Depends(get_asesor_repo),
):
    await asesor_repo.set_codigo_asesor(asesor, codigo_asesor.strip())
    return RedirectResponse("/", status_code=303)
