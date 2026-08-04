import math
from datetime import date, datetime, timezone

from src.domain.ports.llamada_repository import LlamadaRepository


class ObtenerSiguienteCliente:
    """
    Decide qué le toca al asesor. Devuelve un dict discriminado por 'situacion':

    {"situacion": "cliente", "cliente": {...}}
        → hay alguien listo para llamar YA
          (reagendado vencido primero, luego pendiente/reintento por posición)

    {"situacion": "esperando", "total": N, "reagendados": [...]}
        → nadie listo AHORA, pero hay reagendados cuyo tiempo no venció.
          El día NO terminó. Cada item: {nombre, minutos_restantes, hora}.

    {"situacion": "terminado"}
        → no queda absolutamente nadie: ni pendientes, ni reintentos,
          ni reagendados sin vencer.
    """

    def __init__(self, repo: LlamadaRepository):
        self._repo = repo

    async def execute(self, fecha: date, asesor: str) -> dict:
        cliente = await self._repo.get_siguiente_en_cola(fecha, asesor)
        if cliente is not None:
            return {"situacion": "cliente", "cliente": cliente}

        reagendados = await self._repo.get_reagendados_no_vencidos(fecha, asesor)
        if reagendados:
            return {
                "situacion": "esperando",
                "total": len(reagendados),
                "reagendados": [self._con_tiempos(r) for r in reagendados],
            }

        return {"situacion": "terminado"}

    @staticmethod
    def _con_tiempos(reagendado: dict) -> dict:
        """Agrega minutos_restantes (redondeo hacia arriba) y hora local estimada."""
        minutos_restantes = None
        hora = None
        raw = reagendado.get("reagendado_para")
        if raw:
            try:
                vence = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
                delta_seg = (vence - datetime.now(timezone.utc)).total_seconds()
                minutos_restantes = max(1, math.ceil(delta_seg / 60))
                hora = vence.astimezone().strftime("%H:%M")
            except (ValueError, TypeError):
                pass
        return {
            "rutero_cliente_id": reagendado.get("rutero_cliente_id"),
            "nombre": reagendado.get("nombre"),
            "minutos_restantes": minutos_restantes,
            "hora": hora,
        }
