from datetime import date

from src.domain.entities.novedad import Novedad
from src.domain.ports.llamada_repository import LlamadaRepository
from src.domain.value_objects.tipo_novedad import TipoNovedad


class RegistrarNovedad:
    def __init__(self, llamada_repo: LlamadaRepository):
        self._llamada_repo = llamada_repo

    async def execute(
        self,
        rutero_cliente_id: str,
        cliente_id: str,
        tipo: TipoNovedad,
        observacion: str | None,
        fecha: date,
    ) -> Novedad:
        novedad = Novedad(
            rutero_cliente_id=rutero_cliente_id,
            cliente_id=cliente_id,
            fecha=fecha,
            tipo=tipo,
            observacion=observacion,
        )
        novedad = await self._llamada_repo.crear_novedad(novedad)
        return novedad
