import logging
from collections import defaultdict
from datetime import date

from src.domain.entities.llamada import Llamada
from src.domain.ports.asesor_repository import AsesorRepository
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
        asesor_repo: AsesorRepository,
    ):
        self._parser = parser
        self._cliente_repo = cliente_repo
        self._llamada_repo = llamada_repo
        self._asesor_repo = asesor_repo

    async def _filtrar_por_codigo_asesor(self, clientes, codigos_asesor, asesor_televenta):
        """
        Protege contra cargar los clientes de otra asesora (formato nuevo,
        con "COD ASESOR"/"Usuario" por fila). Si el archivo no trae esa
        columna (codigos_asesor vacío), no filtra nada — comportamiento
        idéntico al formato antiguo.

        Devuelve (clientes_filtrados, descartados_por_otro_codigo).
        """
        if not codigos_asesor:
            return clientes, 0

        codigo_configurado = await self._asesor_repo.get_codigo_asesor(asesor_televenta)

        if codigo_configurado:
            if codigo_configurado not in codigos_asesor:
                raise ValueError(
                    f"Tu código de asesora configurado ({codigo_configurado}) no aparece "
                    f"en este archivo. Códigos presentes en el archivo: "
                    f"{', '.join(sorted(codigos_asesor))}."
                )
            codigo_a_usar = codigo_configurado
        elif len(codigos_asesor) == 1:
            codigo_a_usar = next(iter(codigos_asesor))
            await self._asesor_repo.set_codigo_asesor(asesor_televenta, codigo_a_usar)
            log.info(
                "Código de asesora %r configurado automáticamente para %s (único código en el archivo)",
                codigo_a_usar, asesor_televenta,
            )
        else:
            raise ValueError(
                "Este archivo trae varios códigos de asesora "
                f"({', '.join(sorted(codigos_asesor))}) y tu perfil no tiene uno configurado. "
                "Configura tu código en 'Mi código de asesora' antes de cargar este archivo."
            )

        filtrados = [c for c in clientes if c.cod_asesor == codigo_a_usar]
        descartados = len(clientes) - len(filtrados)
        return filtrados, descartados

    async def execute(self, file_bytes: bytes, fecha: date, asesor_televenta: str) -> dict:
        # El "Asesor" del Excel es quien visita a esos clientes en campo, no
        # quien los llama por teléfono — no determina el dueño del rutero.
        # El dueño es siempre quien tiene la sesión abierta al cargar.
        clientes, usuario_id, asesor_campo, codigos_asesor = self._parser.parse(file_bytes)

        clientes, descartados_otro_asesor = await self._filtrar_por_codigo_asesor(
            clientes, codigos_asesor, asesor_televenta
        )

        log.info(
            "Cargando rutero semanal — semana de: %s | asesor televenta: %s | asesor de campo (Excel): %s | "
            "clientes en archivo: %d | descartados por ser de otro código de asesora: %d",
            fecha, asesor_televenta, asesor_campo, len(clientes), descartados_otro_asesor,
        )

        if not clientes:
            return {
                "clientes_cargados": 0,
                "asesor": asesor_televenta,
                "dias": [],
                "sin_dia_definido": 0,
                "descartados_otro_asesor": descartados_otro_asesor,
            }

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
            "descartados_otro_asesor": descartados_otro_asesor,
        }
