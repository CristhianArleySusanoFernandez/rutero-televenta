from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from src.api.dependencies import (
    get_asesor_actual,
    get_obtener_historial_pedidos_cliente,
    get_obtener_sugerencias_pedido,
    get_registrar_pedido,
)
from src.api.templates_config import templates
from src.application.use_cases.obtener_historial_pedidos_cliente import ObtenerHistorialPedidosCliente
from src.application.use_cases.obtener_sugerencias_pedido import ObtenerSugerenciasPedido
from src.application.use_cases.registrar_pedido import RegistrarPedido

router = APIRouter(prefix="/pedidos", tags=["pedidos"])


class RegistrarPedidoBody(BaseModel):
    cliente_id: str
    detalle: str
    rutero_cliente_id: str | None = None
    fecha: date | None = None


@router.post("")
async def registrar_pedido(
    body: RegistrarPedidoBody,
    asesor: str = Depends(get_asesor_actual),
    uc: RegistrarPedido = Depends(get_registrar_pedido),
):
    """
    Registra lo vendido en la llamada actual. No toca el estado del
    cliente en la cola ni crea novedades — solo persiste el pedido.
    """
    try:
        pedido = await uc.execute(
            cliente_id=body.cliente_id,
            detalle=body.detalle,
            asesor=asesor,
            rutero_cliente_id=body.rutero_cliente_id,
            fecha=body.fecha,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return JSONResponse({"ok": True, "fecha": str(pedido.fecha), "detalle": pedido.detalle})


@router.get("/sugerencias")
async def sugerencias_pedido(
    cliente_id: str = Query(...),
    asesor: str = Depends(get_asesor_actual),
    uc: ObtenerSugerenciasPedido = Depends(get_obtener_sugerencias_pedido),
):
    sugerencias = await uc.execute(cliente_id, asesor)
    return JSONResponse({"sugerencias": sugerencias})


@router.get("/{cliente_id}/historial", response_class=HTMLResponse)
async def historial_pedidos_cliente(
    request: Request,
    cliente_id: str,
    uc: ObtenerHistorialPedidosCliente = Depends(get_obtener_historial_pedidos_cliente),
):
    pedidos = await uc.execute(cliente_id)
    return templates.TemplateResponse(
        request,
        "partials/historial_pedidos_cliente.html",
        {"pedidos": pedidos},
    )
