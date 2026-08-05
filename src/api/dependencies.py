from typing import Optional

from fastapi import Request

from src.application.use_cases.cargar_rutero import CargarRutero
from src.application.use_cases.corregir_resultado import CorregirResultado
from src.application.use_cases.eliminar_rutero_dia import EliminarRuteroDia
from src.application.use_cases.exportar_reporte import ExportarReporte
from src.application.use_cases.gestionar_notas_cliente import GestionarNotasCliente
from src.application.use_cases.listar_asesores import ListarAsesores
from src.application.use_cases.obtener_cliente_especifico import ObtenerClienteEspecifico
from src.application.use_cases.obtener_datos_tarjeta_cliente import ObtenerDatosTarjetaCliente
from src.application.use_cases.obtener_historial import ObtenerHistorial
from src.application.use_cases.obtener_rutero_dia import ObtenerRuteroDia
from src.application.use_cases.obtener_siguiente_cliente import ObtenerSiguienteCliente
from src.application.use_cases.ordenar_llamada_cliente import OrdenarLlamadaCliente
from src.application.use_cases.registrar_fin_llamada import RegistrarFinLlamada
from src.application.use_cases.registrar_llamada import RegistrarLlamada
from src.application.use_cases.registrar_no_contesta import RegistrarNoContesta
from src.application.use_cases.registrar_novedad import RegistrarNovedad
from src.application.use_cases.seleccionar_asesor import SeleccionarAsesor
from src.infrastructure.adapters.excel_rutero_parser import ExcelRuteroParser
from src.infrastructure.adapters.supabase_asesor_repository import SupabaseAsesorRepository
from src.infrastructure.adapters.supabase_cliente_repository import SupabaseClienteRepository
from src.infrastructure.adapters.supabase_llamada_repository import SupabaseLlamadaRepository
from src.infrastructure.adapters.supabase_nota_cliente_repository import SupabaseNotaClienteRepository
from src.infrastructure.adapters.websocket_telefono_gateway import WebSocketTelefonoGateway
from src.infrastructure.supabase_client import get_supabase

ASESOR_COOKIE = "asesor"


def get_cliente_repo() -> SupabaseClienteRepository:
    return SupabaseClienteRepository(get_supabase())


def get_llamada_repo() -> SupabaseLlamadaRepository:
    return SupabaseLlamadaRepository(get_supabase())


def get_parser() -> ExcelRuteroParser:
    return ExcelRuteroParser()


def get_cargar_rutero() -> CargarRutero:
    return CargarRutero(get_parser(), get_cliente_repo(), get_llamada_repo())


def get_registrar_llamada() -> RegistrarLlamada:
    return RegistrarLlamada(get_llamada_repo())


def get_registrar_novedad() -> RegistrarNovedad:
    return RegistrarNovedad(get_llamada_repo())


def get_corregir_resultado() -> CorregirResultado:
    return CorregirResultado(get_llamada_repo())


def get_eliminar_rutero_dia() -> EliminarRuteroDia:
    return EliminarRuteroDia(get_llamada_repo())


def get_obtener_rutero_dia() -> ObtenerRuteroDia:
    return ObtenerRuteroDia(get_llamada_repo())


def get_obtener_historial() -> ObtenerHistorial:
    return ObtenerHistorial(get_llamada_repo())


def get_obtener_datos_tarjeta_cliente() -> ObtenerDatosTarjetaCliente:
    return ObtenerDatosTarjetaCliente(get_llamada_repo())


def get_exportar_reporte() -> ExportarReporte:
    return ExportarReporte(get_llamada_repo())


def get_nota_repo() -> SupabaseNotaClienteRepository:
    return SupabaseNotaClienteRepository(get_supabase())


def get_gestionar_notas() -> GestionarNotasCliente:
    return GestionarNotasCliente(get_nota_repo())


def get_obtener_siguiente_cliente() -> ObtenerSiguienteCliente:
    return ObtenerSiguienteCliente(get_llamada_repo())


def get_registrar_no_contesta() -> RegistrarNoContesta:
    return RegistrarNoContesta(get_llamada_repo())


def get_obtener_cliente_especifico() -> ObtenerClienteEspecifico:
    return ObtenerClienteEspecifico(get_llamada_repo())


# ──────────────────────────────────────────────────────────────
# Gateway del teléfono — SINGLETON por proceso.
# A diferencia de los repos (que se crean por request), el gateway
# mantiene el dict de conexiones WebSocket vivas y debe ser único.
# ──────────────────────────────────────────────────────────────

_telefono_gateway = WebSocketTelefonoGateway()


async def _on_llamada_finalizada(llamada_id: str, duracion_seg: int) -> None:
    """Hook: al recibir IDLE del teléfono, guardar la duración en Supabase."""
    await RegistrarFinLlamada(get_llamada_repo()).execute(llamada_id, duracion_seg)


_telefono_gateway.on_llamada_finalizada = _on_llamada_finalizada


def get_telefono_gateway() -> WebSocketTelefonoGateway:
    return _telefono_gateway


def get_ordenar_llamada_cliente() -> OrdenarLlamadaCliente:
    return OrdenarLlamadaCliente(get_llamada_repo(), _telefono_gateway)


# ──────────────────────────────────────────────────────────────
# Identidad del asesor — cookie de sesión, sin autenticación.
# ──────────────────────────────────────────────────────────────

def get_asesor_repo() -> SupabaseAsesorRepository:
    return SupabaseAsesorRepository(get_supabase())


def get_listar_asesores() -> ListarAsesores:
    return ListarAsesores(get_asesor_repo())


def get_seleccionar_asesor() -> SeleccionarAsesor:
    return SeleccionarAsesor(get_asesor_repo())


def get_asesor_actual(request: Request) -> Optional[str]:
    """Nombre del asesor identificado en esta sesión, o None si no ha elegido."""
    return request.cookies.get(ASESOR_COOKIE) or None


def requerir_asesor_actual(request: Request) -> str:
    """Como get_asesor_actual, pero exige que ya esté identificado."""
    nombre = get_asesor_actual(request)
    if not nombre:
        raise ValueError("No hay asesor identificado en esta sesión")
    return nombre
