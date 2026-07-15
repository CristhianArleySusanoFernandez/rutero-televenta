from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from src.api.dependencies import get_gestionar_notas
from src.api.templates_config import templates
from src.application.use_cases.gestionar_notas_cliente import GestionarNotasCliente

router = APIRouter(prefix="/notas", tags=["notas"])


class NotaBody(BaseModel):
    cliente_id: str
    nota: str
    autor: str | None = None


@router.get("/{cliente_id}", response_class=HTMLResponse)
async def listar_notas(
    request: Request,
    cliente_id: str,
    uc: GestionarNotasCliente = Depends(get_gestionar_notas),
):
    notas = await uc.listar(cliente_id)
    return templates.TemplateResponse(
        request,
        "partials/notas_cliente.html",
        {"notas": notas, "cliente_id": cliente_id},
    )


@router.post("", response_class=HTMLResponse)
async def agregar_nota(
    request: Request,
    body: NotaBody,
    uc: GestionarNotasCliente = Depends(get_gestionar_notas),
):
    try:
        await uc.agregar(body.cliente_id, body.nota, body.autor)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    notas = await uc.listar(body.cliente_id)
    return templates.TemplateResponse(
        request,
        "partials/notas_cliente.html",
        {"notas": notas, "cliente_id": body.cliente_id},
    )


@router.delete("/{nota_id}", response_class=HTMLResponse)
async def eliminar_nota(
    request: Request,
    nota_id: str,
    cliente_id: str,
    uc: GestionarNotasCliente = Depends(get_gestionar_notas),
):
    try:
        await uc.eliminar(nota_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    notas = await uc.listar(cliente_id)
    return templates.TemplateResponse(
        request,
        "partials/notas_cliente.html",
        {"notas": notas, "cliente_id": cliente_id},
    )
