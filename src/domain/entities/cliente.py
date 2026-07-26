import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Cliente:
    cod_cliente: str
    nombre: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    documento: Optional[str] = None
    razon_social: Optional[str] = None
    direccion: Optional[str] = None
    barrio: Optional[str] = None
    ciudad: Optional[str] = None
    dias_visita: Optional[str] = None
    telefono: Optional[str] = None
    created_at: Optional[datetime] = None
