from src.domain.ports.llamada_repository import LlamadaRepository


class NovedadNoEncontrada(Exception):
    pass


class NovedadAjena(Exception):
    """La novedad existe pero pertenece a otro asesor (BR-012)."""


class NovedadYaAnulada(Exception):
    pass


class AnularNovedad:
    """
    Anula (soft) una novedad que ya no aplica — ej. el cliente marcó
    'no contestó' y luego devolvió la llamada e hizo pedido. Nunca borra
    la fila; sólo marca anulada=true con un motivo obligatorio.
    """

    def __init__(self, llamada_repo: LlamadaRepository):
        self._llamada_repo = llamada_repo

    async def execute(self, novedad_id: str, asesor: str, motivo: str) -> None:
        motivo_limpio = motivo.strip()
        if not motivo_limpio:
            raise ValueError("El motivo de anulación es obligatorio")

        novedad = await self._llamada_repo.get_novedad_por_id(novedad_id)
        if novedad is None:
            raise NovedadNoEncontrada(f"Novedad '{novedad_id}' no existe")

        # No confiar en lo que manda el navegador: se verifica en el
        # servidor que la novedad pertenece al asesor de la cookie.
        if novedad.get("asesor") != asesor:
            raise NovedadAjena("No puedes anular una novedad de otro asesor")

        if novedad.get("anulada"):
            raise NovedadYaAnulada("Esta novedad ya estaba anulada")

        await self._llamada_repo.anular_novedad(novedad_id, motivo_limpio)
