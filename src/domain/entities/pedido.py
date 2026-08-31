import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class Pedido:
    cliente_id: str
    fecha: date
    detalle: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    rutero_cliente_id: Optional[str] = None
    asesor: Optional[str] = None
    created_at: Optional[datetime] = None
