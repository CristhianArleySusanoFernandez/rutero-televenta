import uuid
from dataclasses import dataclass, field
from datetime import datetime, time
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
    novedad_excel: Optional[str] = None
    asesor_campo: Optional[str] = None
    # Campos del formato nuevo de rutero (ACTUALIZACION_DATOS_TV_*.xlsx).
    # Vienen del Excel, se sobrescriben en cada carga (opción A, igual que
    # el resto de _to_row()). telefono2 solo se guarda y se muestra, NO
    # se integra con la marcación.
    email: Optional[str] = None
    segmento: Optional[str] = None
    telefono2: Optional[str] = None
    observacion_excel: Optional[str] = None
    dato_a_corregir: Optional[str] = None
    # Código de asesora (puesto) de la fila en ESTE archivo — transitorio,
    # solo para que CargarRutero filtre por asesora al cargar; nunca se
    # persiste en `clientes` (no está en _to_row()).
    cod_asesor: Optional[str] = None
    # Franja horaria preferida (permanente, NO viene del Excel — ver
    # _to_row() en supabase_cliente_repository.py, que a propósito NO
    # incluye estos dos campos para que el upsert nunca los sobrescriba).
    franja_desde: Optional[time] = None
    franja_hasta: Optional[time] = None
    created_at: Optional[datetime] = None
