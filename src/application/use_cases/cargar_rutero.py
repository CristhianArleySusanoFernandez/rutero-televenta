import logging
from collections import defaultdict
from datetime import date

from src.domain.entities.llamada import Llamada
from src.domain.ports.cliente_repository import ClienteRepository
from src.domain.ports.llamada_repository import LlamadaRepository
from src.domain.ports.rutero_parser import RuteroParser
from src.domain.servicios.dia_visita import fecha_del_dia_en_semana, parsear_dia_visita

log = logging.getLogger(__name__)


class CargarRutero:
    """
    El archivo trae los clientes de TODA la semana; la columna "Dias Visita"
    indica a qué día de la semana pertenece cada uno. Se reparten en un
    rutero_dia distinto por cada día que aparezca en el archivo (misma
    semana que `fecha`), reutilizando el modelo existente de un rutero_dia
    por (fecha, asesor) — así la cola, las stats y el reporte, que ya
    filtran por fecha, quedan filtrados por día sin tocarlos.

    Clientes cuyo código no termina en un día válido no se descartan: se
    incluyen en TODOS los días con clientes de esa semana, marcados como
    "sin día definido" (calculado al vuelo desde dias_visita, sin columna
    nueva) para que la tarjeta lo muestre y la asesora lo revise.
    """

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
            "Cargando rutero semanal — semana de: %s | asesor televenta: %s | asesor de campo (Excel): %s | clientes en archivo: %d",
            fecha, asesor_televenta, asesor_campo, len(clientes),
        )

        por_dia: dict[int, list] = defaultdict(list)
        sin_dia: list = []
        for cliente in clientes:
            dia = parsear_dia_visita(cliente.dias_visita)
            if dia is None:
                sin_dia.append(cliente)
            else:
                por_dia[dia].append(cliente)

        dias_con_clientes = sorted(por_dia.keys())
        if sin_dia:
            for dia in dias_con_clientes:
                por_dia[dia].extend(sin_dia)
            log.info("Clientes sin día de visita válido: %d — incluidos en todos los días de la semana", len(sin_dia))

        insertados = 0
        dias_cargados = []
        for dia in dias_con_clientes:
            fecha_dia = fecha_del_dia_en_semana(fecha, dia)
            rutero_dia_id = await self._llamada_repo.crear_rutero_dia(fecha_dia, usuario_id, asesor_televenta)

            clientes_del_dia = por_dia[dia]
            mapa_id = await self._cliente_repo.upsert_lote(clientes_del_dia)

            llamadas = []
            for posicion, cliente in enumerate(clientes_del_dia, start=1):
                cod = str(cliente.cod_cliente)
                cliente_id = mapa_id.get(cod)
                if cliente_id is None:
                    raise RuntimeError(
                        f"No se pudo resolver el id del cliente cod_cliente={cod!r} "
                        f"tras el upsert por lotes (rutero_dia_id={rutero_dia_id})"
                    )
                llamadas.append(
                    Llamada(
                        rutero_dia_id=rutero_dia_id,
                        cliente_id=cliente_id,
                        posicion_cola=posicion,
                    )
                )
            await self._llamada_repo.crear_llamadas_lote(llamadas)
            insertados += len(llamadas)

            dias_cargados.append({"fecha": str(fecha_dia), "clientes": len(por_dia[dia])})

        log.info(
            "Rutero semanal cargado — insertados en Supabase: %d | días: %s",
            insertados, dias_cargados,
        )
        return {
            "clientes_cargados": insertados,
            "asesor": asesor_televenta,
            "dias": dias_cargados,
            "sin_dia_definido": len(sin_dia),
        }
