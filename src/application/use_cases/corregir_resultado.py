from datetime import date, datetime

from src.domain.entities.novedad import Novedad
from src.domain.ports.llamada_repository import LlamadaRepository
from src.domain.value_objects.estado_llamada import EstadoLlamada
from src.domain.value_objects.tipo_novedad import TipoNovedad

ESTADOS_CORREGIBLES = {EstadoLlamada.CONTESTO, EstadoLlamada.NO_CONTESTO}


class CorregirResultado:
    """
    Corrige el resultado de un cliente que ya salió de la cola (ej: 'No
    contestó' y luego devolvió la llamada). Solo aplica sobre resultados
    finales, nunca sobre clientes todavía en curso (pendiente, reintento,
    reagendado) — esos se manejan por el flujo normal de cola.
    """

    def __init__(self, llamada_repo: LlamadaRepository):
        self._llamada_repo = llamada_repo

    async def execute(
        self,
        rutero_cliente_id: str,
        cliente_id: str,
        estado_nuevo: EstadoLlamada,
        observacion: str,
        fecha: date,
    ) -> None:
        if estado_nuevo not in ESTADOS_CORREGIBLES:
            raise ValueError("Solo se puede corregir a 'Contestó' o 'No contestó'")

        datos = await self._llamada_repo.get_datos_tarjeta_cliente(rutero_cliente_id)
        estado_actual = EstadoLlamada(datos["estado"])
        if estado_actual not in ESTADOS_CORREGIBLES:
            raise ValueError(
                "Solo se puede corregir un cliente que ya tiene un resultado final"
            )

        await self._llamada_repo.actualizar_estado(rutero_cliente_id, estado_nuevo)

        hora = datetime.now().strftime("%d/%m %H:%M")
        texto = f"[Corrección {hora}] {estado_actual.value} → {estado_nuevo.value}. {observacion}"
        novedad = Novedad(
            rutero_cliente_id=rutero_cliente_id,
            cliente_id=cliente_id,
            fecha=fecha,
            tipo=TipoNovedad.OTRO,
            observacion=texto,
        )
        await self._llamada_repo.crear_novedad(novedad)
