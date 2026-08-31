from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from src.api.dependencies import (
    get_asesor_actual,
    get_cargar_rutero,
    get_eliminar_rutero_dia,
    get_exportar_rutero_excel,
    get_obtener_rutero_dia,
)
from src.api.templates_config import templates
from src.application.use_cases.calcular_stats_rutero import calcular_stats, filtrar_clientes
from src.application.use_cases.cargar_rutero import CargarRutero
from src.application.use_cases.eliminar_rutero_dia import EliminarRuteroDia
from src.application.use_cases.exportar_rutero_excel import ExportarRuteroExcel
from src.application.use_cases.obtener_rutero_dia import ObtenerRuteroDia

router = APIRouter(prefix="/rutero", tags=["rutero"])


@router.post("/cargar")
async def cargar_rutero(
    request: Request,
    archivo: UploadFile = File(...),
    fecha: Optional[date] = Form(None),
    asesor: str = Depends(get_asesor_actual),
    uc: CargarRutero = Depends(get_cargar_rutero),
    uc_dia: ObtenerRuteroDia = Depends(get_obtener_rutero_dia),
):
    if not archivo.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="El archivo debe ser .xlsx")

    fecha_efectiva = fecha or date.today()

    try:
        contenido = await archivo.read()
        resultado = await uc.execute(contenido, fecha_efectiva, asesor)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error al procesar el archivo: {e}")

    clientes = await uc_dia.execute(fecha_efectiva, asesor)
    stats = calcular_stats(clientes)

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
    asesor: str = Depends(get_asesor_actual),
    uc: ObtenerRuteroDia = Depends(get_obtener_rutero_dia),
):
    fecha_efectiva = fecha or date.today()
    clientes = await uc.execute(fecha_efectiva, asesor)
    stats = calcular_stats(clientes)
    clientes = filtrar_clientes(clientes, filtro)

    return templates.TemplateResponse(
        request,
        "partials/lista_clientes.html",
        {"clientes": clientes, "stats": stats, "hoy": fecha_efectiva, "filtro": filtro},
    )


@router.get("/stats", response_class=HTMLResponse)
async def stats_del_dia(
    request: Request,
    fecha: Optional[date] = None,
    asesor: str = Depends(get_asesor_actual),
    uc: ObtenerRuteroDia = Depends(get_obtener_rutero_dia),
):
    fecha_efectiva = fecha or date.today()
    clientes = await uc.execute(fecha_efectiva, asesor)
    return templates.TemplateResponse(
        request,
        "partials/stats_bar.html",
        {"stats": calcular_stats(clientes)},
    )


@router.get("/resumen")
async def resumen_rutero_dia(
    fecha: date,
    asesor: str = Depends(get_asesor_actual),
    uc: EliminarRuteroDia = Depends(get_eliminar_rutero_dia),
):
    return JSONResponse(await uc.resumen(fecha, asesor))


@router.get("/exportar-completo")
async def exportar_rutero_completo(
    fecha: Optional[date] = None,
    asesor: str = Depends(get_asesor_actual),
    uc: ExportarRuteroExcel = Depends(get_exportar_rutero_excel),
):
    """
    Rutero completo de la semana (12 columnas del Excel original), listo
    para corregir y volver a subir. Distinto de /reportes/exportar (que
    exporta solo las excepciones del día con 6 columnas).
    """
    fecha_efectiva = fecha or date.today()
    buffer, nombre_archivo = await uc.execute(fecha_efectiva, asesor)
    headers = {"Content-Disposition": f'attachment; filename="{nombre_archivo}"'}
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.delete("/eliminar")
async def eliminar_rutero_dia(
    fecha: date,
    asesor: str = Depends(get_asesor_actual),
    uc: EliminarRuteroDia = Depends(get_eliminar_rutero_dia),
):
    borrado = await uc.execute(fecha, asesor)
    if not borrado:
        raise HTTPException(status_code=404, detail="No hay rutero cargado para esta fecha")
    return JSONResponse({"eliminado": True})
