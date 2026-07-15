import math
from datetime import datetime, timezone
from typing import Optional

from src.domain.ports.llamada_repository import LlamadaRepository


class ObtenerClienteEspecifico:
    """
    Trae UN cliente concreto de la cola para atenderlo fuera del orden normal
    (caso principal: 'Atender ahora' un reagendado cuyo tiempo no venció).

    Devuelve None si el cliente no existe o ya está en un estado final
    (contesto / no_contesto) — el llamador debe caer al flujo normal.

    Si el cliente está reagendado con vencimiento en el futuro, agrega:
      adelantado=True, minutos_faltantes=X (redondeo hacia arriba)
    para que la vista muestre "se adelantó, faltaban X min".
    """

    _ESTADOS_FINALES = {"contesto", "no_contesto"}

    def __init__(self, repo: LlamadaRepository):
        self._repo = repo

    async def execute(self, rutero_cliente_id: str) -> Optional[dict]:
        cliente = await self._repo.get_cliente_de_cola(rutero_cliente_id)
        if cliente is None or cliente.get("estado") in self._ESTADOS_FINALES:
            return None

        if cliente.get("estado") == "reagendado":
            minutos = self._minutos_hasta(cliente.get("reagendado_para"))
            if minutos is not None and minutos > 0:
                cliente["adelantado"] = True
                cliente["minutos_faltantes"] = minutos

        return cliente

    @staticmethod
    def _minutos_hasta(reagendado_para) -> Optional[int]:
        if not reagendado_para:
            return None
        try:
            vence = datetime.fromisoformat(str(reagendado_para).replace("Z", "+00:00"))
            delta_seg = (vence - datetime.now(timezone.utc)).total_seconds()
            return math.ceil(delta_seg / 60) if delta_seg > 0 else 0
        except (ValueError, TypeError):
            return None
