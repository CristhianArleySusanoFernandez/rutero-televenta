from calendar import monthrange
from datetime import date, timedelta
from typing import Optional

from src.application.use_cases.corregir_resultado import PREFIJO_CORRECCION
from src.domain.ports.llamada_repository import LlamadaRepository
from src.domain.servicios.fecha_colombia import hoy_colombia

PERIODOS_VALIDOS = {"dia", "semana", "mes"}


def _rango_periodo(periodo: str, fecha: date) -> tuple[date, date]:
    if periodo == "dia":
        return fecha, fecha
    if periodo == "semana":
        lunes = fecha - timedelta(days=fecha.weekday())
        domingo = lunes + timedelta(days=6)
        return lunes, domingo
    if periodo == "mes":
        primero = fecha.replace(day=1)
        ultimo_dia = monthrange(fecha.year, fecha.month)[1]
        return primero, fecha.replace(day=ultimo_dia)
    raise ValueError(f"Período no soportado: {periodo!r}")


class ObtenerDashboardNovedades:
    """
    Agrega en Python (no hay GROUP BY vía PostgREST, DEC-002) las novedades
    del asesor de la sesión en un período dado, excluyendo anuladas y las
    correcciones de resultado (auditoría, no novedades comerciales).
    """

    def __init__(self, llamada_repo: LlamadaRepository):
        self._llamada_repo = llamada_repo

    async def execute(
        self, asesor: str, periodo: str = "dia", fecha: Optional[date] = None
    ) -> dict:
        if periodo not in PERIODOS_VALIDOS:
            raise ValueError(f"Período no soportado: {periodo!r}")

        fecha_efectiva = fecha or hoy_colombia()
        fecha_desde, fecha_hasta = _rango_periodo(periodo, fecha_efectiva)

        filas = await self._llamada_repo.get_novedades_rango(asesor, fecha_desde, fecha_hasta)
        sin_asesor = await self._llamada_repo.contar_novedades_sin_asesor(fecha_desde, fecha_hasta)

        correcciones_excluidas = 0
        conteo_por_tipo: dict[str, int] = {}
        for fila in filas:
            observacion = fila.get("observacion") or ""
            if observacion.startswith(PREFIJO_CORRECCION):
                correcciones_excluidas += 1
                continue
            tipo = fila["tipo"]
            conteo_por_tipo[tipo] = conteo_por_tipo.get(tipo, 0) + 1

        total = sum(conteo_por_tipo.values())
        por_tipo = sorted(conteo_por_tipo.items(), key=lambda kv: kv[1], reverse=True)

        return {
            "periodo": periodo,
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
            "total": total,
            "por_tipo": por_tipo,
            "correcciones_excluidas": correcciones_excluidas,
            "sin_asesor": sin_asesor,
        }
