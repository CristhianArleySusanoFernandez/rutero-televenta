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
        asesor: str | None = None,
    ) -> Novedad:
        novedad = Novedad(
            rutero_cliente_id=rutero_cliente_id,
            cliente_id=cliente_id,
            fecha=fecha,
            tipo=tipo,
            observacion=observacion,
            asesor=asesor,
        )
        # No se toca el estado del rutero_cliente: 'estado' es solo el
        # resultado de la llamada (contestó/no contestó/etc). La novedad
        # vive aparte en su propia tabla, así un cliente puede haber
        # contestado Y tener una novedad al mismo tiempo.
        return await self._llamada_repo.crear_novedad(novedad)
