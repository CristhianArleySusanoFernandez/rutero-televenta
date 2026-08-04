from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from src.api.dependencies import ASESOR_COOKIE, get_listar_asesores, get_seleccionar_asesor
from src.api.templates_config import templates
from src.application.use_cases.listar_asesores import ListarAsesores
from src.application.use_cases.seleccionar_asesor import SeleccionarAsesor

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
