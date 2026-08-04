import uuid

from fastapi import APIRouter, Depends, WebSocket
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from src.api.dependencies import get_asesor_actual, get_asesor_repo, get_telefono_gateway
from src.domain.ports.asesor_repository import AsesorRepository

router = APIRouter(tags=["telefono"])

# Singleton compartido: vive en dependencies.py (composition root),
# donde también se cablea el hook on_llamada_finalizada.
_gateway = get_telefono_gateway()


# ─────────────────────────────────────────────────────────────
# WebSocket — punto de entrada para la app Android
# ─────────────────────────────────────────────────────────────

@router.websocket("/ws/telefono")
async def ws_telefono(websocket: WebSocket):
    """
    Punto de conexión para la app Android.

    Flujo esperado (contrato §3):
      1. La app abre la conexión.
      2. Envía 'registro' como primer mensaje.
      3. Envía 'disponible' cuando está lista.
      4. Envía 'salud' cada 30s.
      5. Responde a 'llamar' con 'estado_llamada OFFHOOK' y luego 'IDLE'.
    """
    await _gateway.conectar(websocket)


# ─────────────────────────────────────────────────────────────
# REST — panel de estado
# ─────────────────────────────────────────────────────────────

@router.get("/telefono/estado")
async def listar_telefonos(
    asesor: str = Depends(get_asesor_actual),
    asesor_repo: AsesorRepository = Depends(get_asesor_repo),
):
    """
    Devuelve el estado de ÚNICAMENTE el teléfono vinculado al asesor de la
    sesión actual — no los de las demás asesoras.
    """
    telefono_id = await asesor_repo.get_telefono_id(asesor)
    if not telefono_id:
        return JSONResponse([])
    sesion = _gateway.get_sesion(telefono_id)
    return JSONResponse([sesion.to_dict()] if sesion else [])


@router.get("/telefono/{telefono_id}/estado")
async def estado_telefono(telefono_id: str):
    """Estado de un teléfono específico."""
    sesion = _gateway.get_sesion(telefono_id)
    if sesion is None:
        return JSONResponse({"error": f"'{telefono_id}' no está conectado"}, status_code=404)
    return JSONResponse(sesion.to_dict())


# ─────────────────────────────────────────────────────────────
# REST — órdenes al teléfono
# ─────────────────────────────────────────────────────────────

class LlamarBody(BaseModel):
    numero: str
    nombre_contacto: Optional[str] = None


class ColgarBody(BaseModel):
    llamada_id: str


@router.post("/telefono/{telefono_id}/llamar")
async def ordenar_llamada(telefono_id: str, body: LlamarBody):
    """
    El asesor confirma que quiere llamar.
    Genera un llamada_id UUID y envía la orden 'llamar' al teléfono (contrato §5.1).

    El teléfono debe estar registrado y disponible; si no, devuelve 409.
    """
    sesion = _gateway.get_sesion(telefono_id)
    if sesion is None:
        return JSONResponse(
            {"error": f"'{telefono_id}' no está conectado"},
            status_code=404,
        )
    if not sesion.disponible:
        return JSONResponse(
            {
                "error": f"'{telefono_id}' no está disponible",
                "en_llamada": sesion.en_llamada,
                "conectado": sesion.conectado,
            },
            status_code=409,
        )

    llamada_id = str(uuid.uuid4())
    try:
        await _gateway.ordenar_llamada(
            telefono_id=telefono_id,
            llamada_id=llamada_id,
            numero=body.numero,
            nombre_contacto=body.nombre_contacto,
        )
    except RuntimeError as e:
        return JSONResponse({"error": str(e)}, status_code=409)

    return JSONResponse({"ok": True, "llamada_id": llamada_id})


@router.post("/telefono/{telefono_id}/colgar")
async def ordenar_colgar(telefono_id: str, body: ColgarBody):
    """
    Envía orden 'colgar' al teléfono (contrato §5.2).
    Mejor esfuerzo: puede que Android no lo cumpla sin ser app de teléfono por defecto.
    """
    sesion = _gateway.get_sesion(telefono_id)
    if sesion is None:
        return JSONResponse(
            {"error": f"'{telefono_id}' no está conectado"},
            status_code=404,
        )

    try:
        await _gateway.ordenar_colgar(
            telefono_id=telefono_id,
            llamada_id=body.llamada_id,
        )
    except RuntimeError as e:
        return JSONResponse({"error": str(e)}, status_code=409)

    return JSONResponse({"ok": True})
