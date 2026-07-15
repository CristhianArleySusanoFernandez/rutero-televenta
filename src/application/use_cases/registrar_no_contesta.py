from datetime import date

from src.domain.ports.llamada_repository import LlamadaRepository


class RegistrarNoContesta:
    def __init__(self, repo: LlamadaRepository):
        self._repo = repo

    async def execute(self, rutero_cliente_id: str, fecha: date) -> dict:
        """
        1er no-contesta → reintento_pendiente, +4 posiciones en cola.
        2do no-contesta → no_contesto definitivo.
        Devuelve {'estado': ..., 'contador_intentos': ...}
        """
        return await self._repo.registrar_no_contesta_con_reintento(rutero_cliente_id, fecha)
