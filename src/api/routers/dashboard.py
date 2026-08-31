from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse

from src.api.dependencies import get_asesor_actual, get_obtener_dashboard_novedades
from src.api.templates_config import templates
from src.application.use_cases.obtener_dashboard_novedades import (
    PERIODOS_VALIDOS,
    ObtenerDashboardNovedades,
)
from src.domain.servicios.fecha_colombia import hoy_colombia

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/novedades", response_class=HTMLResponse)
async def dashboard_novedades(
    request: Request,
    periodo: str = Query("dia"),
    fecha: date | None = Query(None),
    asesor: str = Depends(get_asesor_actual),
    uc: ObtenerDashboardNovedades = Depends(get_obtener_dashboard_novedades),
):
    if periodo not in PERIODOS_VALIDOS:
        periodo = "dia"
    fecha_efectiva = fecha or hoy_colombia()

    resultado = await uc.execute(asesor, periodo, fecha_efectiva)

    return templates.TemplateResponse(
        request,
        "dashboard_novedades.html",
        {"resultado": resultado, "periodo": periodo, "fecha": fecha_efectiva},
    )
