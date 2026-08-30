from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from src.api.dependencies import (
    get_asesor_actual,
    get_corregir_resultado,
    get_obtener_datos_tarjeta_cliente,
    get_obtener_historial,
    get_registrar_llamada,
    get_registrar_novedad,
)
from src.api.templates_config import templates
from src.application.use_cases.corregir_resultado import CorregirResultado
from src.application.use_cases.obtener_datos_tarjeta_cliente import ObtenerDatosTarjetaCliente
from src.application.use_cases.obtener_historial import ObtenerHistorial
from src.application.use_cases.registrar_llamada import RegistrarLlamada
from src.application.use_cases.registrar_novedad import RegistrarNovedad
from src.domain.servicios.fecha_colombia import hoy_colombia
from src.domain.value_objects.estado_llamada import EstadoLlamada
from src.domain.value_objects.tipo_novedad import TipoNovedad

router = APIRouter(prefix="/llamadas", tags=["llamadas"])


class EstadoBody(BaseModel):
    estado: EstadoLlamada


class NovedadBody(BaseModel):
    cliente_id: str
    tipo: TipoNovedad
    observacion: str | None = None
    fecha: date | None = None


class CorregirResultadoBody(BaseModel):
    cliente_id: str
    estado_nuevo: EstadoLlamada
    observacion: str
    fecha: date | None = None


@router.patch("/{rutero_cliente_id}/estado", response_class=HTMLResponse)
async def actualizar_estado(
    request: Request,
    rutero_cliente_id: str,
    body: EstadoBody,
    uc: RegistrarLlamada = Depends(get_registrar_llamada),
    uc_tarjeta: ObtenerDatosTarjetaCliente = Depends(get_obtener_datos_tarjeta_cliente),
):
    try:
        await uc.execute(rutero_cliente_id, body.estado)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    cliente_data = await uc_tarjeta.execute(rutero_cliente_id)
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
    asesor: str = Depends(get_asesor_actual),
    uc: RegistrarNovedad = Depends(get_registrar_novedad),
    uc_tarjeta: ObtenerDatosTarjetaCliente = Depends(get_obtener_datos_tarjeta_cliente),
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
            fecha=body.fecha or hoy_colombia(),
            asesor=asesor,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    cliente_data = await uc_tarjeta.execute(rutero_cliente_id)
    return templates.TemplateResponse(
        request,
        "partials/cliente_card.html",
        {"cliente": cliente_data},
    )


@router.post("/{rutero_cliente_id}/corregir-resultado", response_class=HTMLResponse)
async def corregir_resultado(
    request: Request,
    rutero_cliente_id: str,
    body: CorregirResultadoBody,
    asesor: str = Depends(get_asesor_actual),
    uc: CorregirResultado = Depends(get_corregir_resultado),
    uc_tarjeta: ObtenerDatosTarjetaCliente = Depends(get_obtener_datos_tarjeta_cliente),
):
    if not body.observacion.strip():
        raise HTTPException(status_code=400, detail="La observación es obligatoria")

    try:
        await uc.execute(
            rutero_cliente_id=rutero_cliente_id,
            cliente_id=body.cliente_id,
            estado_nuevo=body.estado_nuevo,
            observacion=body.observacion.strip(),
            fecha=body.fecha or hoy_colombia(),
            asesor=asesor,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    cliente_data = await uc_tarjeta.execute(rutero_cliente_id)
    return templates.TemplateResponse(
        request,
        "partials/cliente_card.html",
        {"cliente": cliente_data},
    )


@router.get("/{rutero_cliente_id}/corregir-form", response_class=HTMLResponse)
async def corregir_form(
    request: Request,
    rutero_cliente_id: str,
    cliente_id: str,
    estado_actual: str,
):
    return templates.TemplateResponse(
        request,
        "partials/corregir_form.html",
        {
            "rutero_cliente_id": rutero_cliente_id,
            "cliente_id": cliente_id,
            "estado_actual": estado_actual,
        },
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
