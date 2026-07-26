import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class NotaCliente:
    cliente_id: str
    nota: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    autor: Optional[str] = None
    created_at: Optional[datetime] = None
