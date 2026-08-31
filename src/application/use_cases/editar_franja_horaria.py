from datetime import time
from typing import Optional

from src.domain.ports.cliente_repository import ClienteRepository


class EditarFranjaHoraria:
    """
    Registra, cambia o borra la franja horaria preferida de un cliente.
    No toca el estado del cliente en la cola ni registra novedades — es
    un dato permanente del cliente, independiente de la llamada en curso.
    """

    def __init__(self, cliente_repo: ClienteRepository):
        self._cliente_repo = cliente_repo

    async def execute(
        self, cliente_id: str, franja_desde: Optional[time], franja_hasta: Optional[time]
    ) -> None:
        if franja_desde is not None and franja_hasta is not None:
            if franja_desde >= franja_hasta:
                raise ValueError("La hora de inicio debe ser anterior a la hora de fin")
        elif franja_desde is not None or franja_hasta is not None:
            # Dato incompleto: se trata igual que "sin preferencia" en la
            # lectura (esta_fuera_de_franja), pero al guardar preferimos
            # avisar en vez de persistir a medias en silencio.
            raise ValueError("Debes indicar ambas horas, o dejar ambas vacías para borrar la preferencia")

        await self._cliente_repo.actualizar_franja_horaria(cliente_id, franja_desde, franja_hasta)
