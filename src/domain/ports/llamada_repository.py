from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from src.domain.entities.llamada import Llamada
from src.domain.entities.novedad import Novedad
from src.domain.value_objects.estado_llamada import EstadoLlamada


class LlamadaRepository(ABC):
    @abstractmethod
    async def crear_rutero_dia(self, fecha: date, usuario_id: str, asesor: str) -> str:
        """Crea un registro de rutero_dias y retorna su id."""
        ...

    @abstractmethod
    async def get_rutero_dia_id(self, fecha: date) -> Optional[str]:
        """Obtiene el id del rutero del día o None si no existe."""
        ...

    @abstractmethod
    async def crear_llamada(self, llamada: Llamada) -> Llamada:
        """Inserta un rutero_cliente y retorna la entidad con id asignado."""
        ...

    @abstractmethod
    async def actualizar_estado(self, rutero_cliente_id: str, estado: EstadoLlamada) -> Llamada:
        ...

    @abstractmethod
    async def get_llamadas_del_dia(self, fecha: date) -> List[dict]:
        """Retorna lista de dicts con info del cliente + estado + ultima novedad."""
        ...

    @abstractmethod
    async def crear_novedad(self, novedad: Novedad) -> Novedad:
        ...

    @abstractmethod
    async def get_problematicos_del_dia(self, fecha: date) -> List[dict]:
        """
        Clientes del rutero de esa fecha que requieren una decisión: tienen
        al menos una novedad registrada (independientemente del estado —
        un cliente puede haber contestado y aun así tener novedad), o
        quedaron en 'no_contesto' sin novedad (2do intento fallido, sin
        más contexto). Excluye 'contesto' sin novedad y estados en curso
        (pendiente, reagendado, etc.).
        Cada dict: {'nombre', 'razon_social', 'telefono', 'estado_reporte'
        ('No contestó'|'Saltado'|'Novedad'), 'tipo_novedad', 'observacion'}.
        """
        ...

    @abstractmethod
    async def get_historial_novedades(self, cliente_id: str) -> List[Novedad]:
        ...

    @abstractmethod
    async def get_siguiente_en_cola(self, fecha: date) -> Optional[dict]:
        """Devuelve el siguiente cliente a llamar (reagendado vencido → pendiente/reintento)."""
        ...

    @abstractmethod
    async def registrar_no_contesta_con_reintento(
        self, rutero_cliente_id: str, fecha: date
    ) -> dict:
        """
        Aplica la lógica de reintentos:
        - 1er intento fallido → estado reintento_pendiente, reinserta +4 posiciones
        - 2do intento fallido → estado no_contesto definitivo
        Devuelve {'estado': ..., 'contador_intentos': ...}
        """
        ...

    @abstractmethod
    async def reagendar(
        self, rutero_cliente_id: str, minutos: int, fecha: date
    ) -> None:
        """Marca el cliente como reagendado y guarda reagendado_para = now + minutos."""
        ...

    @abstractmethod
    async def get_datos_tarjeta_cliente(self, rutero_cliente_id: str) -> dict:
        """
        Datos de un rutero_cliente para repintar su tarjeta tras una acción
        (cambio de estado, novedad registrada): cliente, última novedad y
        notas permanentes.
        """
        ...

    @abstractmethod
    async def get_cliente_de_cola(self, rutero_cliente_id: str) -> Optional[dict]:
        """
        Devuelve UN cliente específico de la cola con la misma forma enriquecida
        que get_siguiente_en_cola (incluye reagendado_para crudo), o None si no existe.
        Sin decisiones: la atendibilidad la juzga el caso de uso.
        """
        ...

    @abstractmethod
    async def get_reagendados_no_vencidos(self, fecha: date) -> List[dict]:
        """
        Clientes en estado 'reagendado' cuyo reagendado_para AÚN no venció,
        ordenados por vencimiento ascendente.
        Cada dict: {'rutero_cliente_id', 'nombre', 'reagendado_para'}.
        """
        ...

    @abstractmethod
    async def get_datos_para_llamar(self, rutero_cliente_id: str) -> dict:
        """
        Devuelve {'telefono': str, 'nombre': str} del cliente asociado.
        Lanza ValueError si el rutero_cliente no existe.
        """
        ...

    @abstractmethod
    async def asociar_llamada_telefono(self, rutero_cliente_id: str, llamada_id: str) -> None:
        """Guarda el llamada_id (UUID de la orden 'llamar') en el rutero_cliente."""
        ...

    @abstractmethod
    async def guardar_duracion_llamada(self, llamada_id: str, duracion_seg: int) -> None:
        """Guarda la duración reportada en el IDLE, buscando por llamada_id."""
        ...
