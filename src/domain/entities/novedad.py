import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from src.domain.value_objects.tipo_novedad import TipoNovedad


@dataclass
class Novedad:
    rutero_cliente_id: str
    cliente_id: str
    fecha: date
    tipo: TipoNovedad
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    observacion: Optional[str] = None
    created_at: Optional[datetime] = None
