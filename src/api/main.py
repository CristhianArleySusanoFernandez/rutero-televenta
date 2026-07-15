import logging
from contextlib import asynccontextmanager
from datetime import date

logging.basicConfig(level=logging.INFO, format="%(levelname)s [%(name)s] %(message)s")

from typing import Optional

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse

from src.api.dependencies import get_obtener_rutero_dia
from src.api.routers import cola, llamadas, notas, reportes, rutero, telefono
from src.api.templates_config import templates
from src.application.use_cases.obtener_rutero_dia import ObtenerRuteroDia
from src.domain.value_objects.tipo_novedad import TipoNovedad


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Rutero Televenta — Distribuciones Santiago De Tunja", lifespan=lifespan)

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
    uc: ObtenerRuteroDia = Depends(get_obtener_rutero_dia),
):
    fecha_efectiva = fecha or date.today()
    clientes = await uc.execute(fecha_efectiva)

    total = len(clientes)
    contesto = sum(1 for c in clientes if c["estado"] == "contesto")
    no_contesto = sum(1 for c in clientes if c["estado"] == "no_contesto")
    novedad = sum(1 for c in clientes if c["estado"] == "novedad")
    pendiente = sum(1 for c in clientes if c["estado"] == "pendiente")
    llamados = total - pendiente
    progreso = round((llamados / total * 100) if total else 0)

    stats = {
        "total": total,
        "contesto": contesto,
        "no_contesto": no_contesto,
        "novedad": novedad,
        "pendiente": pendiente,
        "llamados": llamados,
        "progreso": progreso,
    }

    clientes_filtrados = clientes if filtro == "todos" else [c for c in clientes if c["estado"] == filtro]

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
