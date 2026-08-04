import logging
from contextlib import asynccontextmanager
from datetime import date
from typing import Optional

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from src.api.dependencies import ASESOR_COOKIE, get_asesor_actual, get_obtener_rutero_dia
from src.api.routers import asesor, cola, llamadas, notas, reportes, rutero, telefono
from src.api.templates_config import templates
from src.application.use_cases.calcular_stats_rutero import calcular_stats, filtrar_clientes
from src.application.use_cases.obtener_rutero_dia import ObtenerRuteroDia
from src.domain.value_objects.tipo_novedad import TipoNovedad

logging.basicConfig(level=logging.INFO, format="%(levelname)s [%(name)s] %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Rutero Televenta — Distribuciones Santiago De Tunja", lifespan=lifespan)


@app.middleware("http")
async def requerir_asesor_identificado(request: Request, call_next):
    """
    Sin asesor identificado, cualquier ruta que no sea /asesor/* o /ws/*
    redirige a la pantalla de selección — no hay auth, pero sí identidad.
    """
    path = request.url.path
    exento = path.startswith("/asesor") or path.startswith("/ws")
    if not exento and ASESOR_COOKIE not in request.cookies:
        return RedirectResponse("/asesor/seleccionar")
    return await call_next(request)


app.include_router(asesor.router)
app.include_router(rutero.router)
app.include_router(cola.router)
app.include_router(llamadas.router)
app.include_router(notas.router)
app.include_router(reportes.router)
app.include_router(telefono.router)


@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    filtro: str = "todos",
    fecha: Optional[date] = None,
    asesor: str = Depends(get_asesor_actual),
    uc: ObtenerRuteroDia = Depends(get_obtener_rutero_dia),
):
    fecha_efectiva = fecha or date.today()
    clientes = await uc.execute(fecha_efectiva, asesor)

    stats = calcular_stats(clientes)
    clientes_filtrados = filtrar_clientes(clientes, filtro)

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "clientes": clientes_filtrados,
            "stats": stats,
            "hoy": fecha_efectiva,
            "filtro": filtro,
            "tipos_novedad": [t.value for t in TipoNovedad],
        },
    )
