import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class CambioCliente:
    cliente_id: str
    campo: str
    fecha: date
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    asesor: Optional[str] = None
    valor_anterior: Optional[str] = None
    valor_nuevo: Optional[str] = None
    created_at: Optional[datetime] = None
