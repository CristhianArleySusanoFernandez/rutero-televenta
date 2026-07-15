from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse

from src.api.dependencies import get_cargar_rutero, get_obtener_rutero_dia
from src.api.templates_config import templates
from src.application.use_cases.cargar_rutero import CargarRutero
from src.application.use_cases.obtener_rutero_dia import ObtenerRuteroDia

router = APIRouter(prefix="/rutero", tags=["rutero"])


@router.post("/cargar")
async def cargar_rutero(
    request: Request,
    archivo: UploadFile = File(...),
    fecha: Optional[date] = Form(None),
    uc: CargarRutero = Depends(get_cargar_rutero),
    uc_dia: ObtenerRuteroDia = Depends(get_obtener_rutero_dia),
):
    if not archivo.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="El archivo debe ser .xlsx")

    fecha_efectiva = fecha or date.today()

    try:
        contenido = await archivo.read()
        resultado = await uc.execute(contenido, fecha_efectiva)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error al procesar el archivo: {e}")

    clientes = await uc_dia.execute(fecha_efectiva)
    stats = _calcular_stats(clientes)

    is_htmx = request.headers.get("HX-Request")
    if is_htmx:
        return templates.TemplateResponse(
            request,
            "partials/lista_clientes.html",
            {"clientes": clientes, "stats": stats, "hoy": fecha_efectiva},
        )
    return resultado


@router.get("/hoy", response_class=HTMLResponse)
async def rutero_hoy(
    request: Request,
    filtro: str = "todos",
    fecha: Optional[date] = None,
    uc: ObtenerRuteroDia = Depends(get_obtener_rutero_dia),
):
    fecha_efectiva = fecha or date.today()
    clientes = await uc.execute(fecha_efectiva)
    stats = _calcular_stats(clientes)

    if filtro != "todos":
        clientes = [c for c in clientes if c["estado"] == filtro]

    return templates.TemplateResponse(
        request,
        "partials/lista_clientes.html",
        {"clientes": clientes, "stats": stats, "hoy": fecha_efectiva, "filtro": filtro},
    )


def _calcular_stats(clientes: list) -> dict:
    total = len(clientes)
    contesto = sum(1 for c in clientes if c["estado"] == "contesto")
    no_contesto = sum(1 for c in clientes if c["estado"] == "no_contesto")
    novedad = sum(1 for c in clientes if c["estado"] == "novedad")
    pendiente = sum(1 for c in clientes if c["estado"] == "pendiente")
    llamados = total - pendiente
    progreso = round((llamados / total * 100) if total else 0)
    return {
        "total": total,
        "contesto": contesto,
        "no_contesto": no_contesto,
        "novedad": novedad,
        "pendiente": pendiente,
        "llamados": llamados,
        "progreso": progreso,
    }
