import logging
from datetime import date

from src.domain.entities.llamada import Llamada
from src.domain.ports.cliente_repository import ClienteRepository
from src.domain.ports.llamada_repository import LlamadaRepository
from src.domain.ports.rutero_parser import RuteroParser

log = logging.getLogger(__name__)


class CargarRutero:
    def __init__(
        self,
        parser: RuteroParser,
        cliente_repo: ClienteRepository,
        llamada_repo: LlamadaRepository,
    ):
        self._parser = parser
        self._cliente_repo = cliente_repo
        self._llamada_repo = llamada_repo

    async def execute(self, file_bytes: bytes, fecha: date, asesor_televenta: str) -> dict:
        # El "Asesor" del Excel es quien visita a esos clientes en campo, no
        # quien los llama por teléfono — no determina el dueño del rutero.
        # El dueño es siempre quien tiene la sesión abierta al cargar.
        clientes, usuario_id, asesor_campo = self._parser.parse(file_bytes)

        log.info(
            "Cargando rutero — fecha: %s | asesor televenta: %s | asesor de campo (Excel): %s | clientes a insertar: %d",
            fecha, asesor_televenta, asesor_campo, len(clientes),
        )

        rutero_dia_id = await self._llamada_repo.crear_rutero_dia(fecha, usuario_id, asesor_televenta)

        insertados = 0
        for posicion, cliente in enumerate(clientes, start=1):
            cliente_guardado = await self._cliente_repo.upsert(cliente)
            llamada = Llamada(
                rutero_dia_id=rutero_dia_id,
                cliente_id=cliente_guardado.id,
                posicion_cola=posicion,
            )
            await self._llamada_repo.crear_llamada(llamada)
            insertados += 1

        log.info(
            "Rutero cargado — fecha: %s | insertados en Supabase: %d",
            fecha, insertados,
        )
        return {"fecha": str(fecha), "clientes_cargados": insertados, "asesor": asesor_televenta}
