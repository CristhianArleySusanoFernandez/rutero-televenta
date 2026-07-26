import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from src.domain.value_objects.estado_llamada import EstadoLlamada


@dataclass
class Llamada:
    rutero_dia_id: str
    cliente_id: str
    estado: EstadoLlamada = EstadoLlamada.PENDIENTE
    posicion_cola: Optional[int] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    updated_at: Optional[datetime] = None
