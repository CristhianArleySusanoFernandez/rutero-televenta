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
    async def get_rutero_dia_id(self, fecha: date, asesor: str) -> Optional[str]:
        """Obtiene el id del rutero de ese asesor para esa fecha, o None si no existe."""
        ...

    @abstractmethod
    async def crear_llamada(self, llamada: Llamada) -> Llamada:
        """Inserta un rutero_cliente y retorna la entidad con id asignado."""
        ...

    @abstractmethod
    async def crear_llamadas_lote(self, llamadas: List[Llamada]) -> None:
        """
        Upsert masivo de rutero_clientes (on_conflict=rutero_dia_id,cliente_id,
        ignore_duplicates=True) — misma semántica que crear_llamada pero para
        una lista completa: no pisa el progreso de filas ya existentes (BR-013).
        """
        ...

    @abstractmethod
    async def actualizar_estado(self, rutero_cliente_id: str, estado: EstadoLlamada) -> Llamada:
        ...

    @abstractmethod
    async def get_llamadas_del_dia(self, fecha: date, asesor: str) -> List[dict]:
        """Retorna lista de dicts con info del cliente + estado + ultima novedad."""
        ...

    @abstractmethod
    async def crear_novedad(self, novedad: Novedad) -> Novedad:
        ...

    @abstractmethod
    async def get_problematicos_del_dia(self, fecha: date, asesor: str) -> List[dict]:
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
    async def get_siguiente_en_cola(self, fecha: date, asesor: str) -> Optional[dict]:
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
    async def get_reagendados_no_vencidos(self, fecha: date, asesor: str) -> List[dict]:
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

    @abstractmethod
    async def contar_rutero_dia(self, fecha: date, asesor: str) -> dict:
        """
        {'total': N, 'ya_llamados': M} del rutero de esa fecha+asesor.
        ya_llamados = clientes en estado contesto o no_contesto.
        Si no existe el rutero_dia, retorna {'total': 0, 'ya_llamados': 0}.
        """
        ...

    @abstractmethod
    async def get_novedades_rango(
        self, asesor: str, fecha_desde: date, fecha_hasta: date
    ) -> List[dict]:
        """
        Novedades de ese asesor con fecha entre fecha_desde y fecha_hasta
        (ambas inclusive), excluyendo anuladas. Cada dict trae al menos
        'tipo', 'observacion', 'cliente_id', 'fecha'.
        """
        ...

    @abstractmethod
    async def contar_novedades_sin_asesor(self, fecha_desde: date, fecha_hasta: date) -> int:
        """
        Conteo de novedades sin asesor asignado (asesor IS NULL, no anuladas)
        en el rango de fechas — filas históricas previas a la migración que
        pobló 'asesor'. No se puede saber de quién son, solo cuántas hay.
        """
        ...

    @abstractmethod
    async def get_historial_novedades_por_asesor(self, cliente_id: str, asesor: str) -> List[dict]:
        """
        Historial de novedades de ese cliente, restringido a las que
        pertenecen a `asesor` (BR-012) — incluye anuladas (se muestran
        marcadas, no se ocultan). Cada dict trae al menos 'id', 'fecha',
        'tipo', 'observacion', 'anulada', 'anulada_motivo', 'created_at'.
        """
        ...

    @abstractmethod
    async def get_novedad_por_id(self, novedad_id: str) -> Optional[dict]:
        """
        Devuelve la novedad cruda (dict, incluye 'asesor' y 'anulada') o
        None si no existe. Usado para verificar propiedad antes de anular.
        """
        ...

    @abstractmethod
    async def anular_novedad(self, novedad_id: str, motivo: str) -> None:
        """
        Marca anulada=true y guarda anulada_motivo. No borra la fila.
        No verifica propiedad ni si ya estaba anulada — eso es
        responsabilidad del caso de uso, que ya consultó get_novedad_por_id.
        """
        ...

    @abstractmethod
    async def get_clientes_semana(self, fecha_desde: date, fecha_hasta: date, asesor: str) -> List[dict]:
        """
        Clientes de los rutero_dias de ese asesor entre fecha_desde y
        fecha_hasta (ambas inclusive), para exportar el rutero completo
        (no la tabla `clientes` entera, que es global). Un cliente que
        aparece en varios días de la semana (BR-011, sin día válido) sale
        UNA sola vez. Cada dict trae los campos del cliente más
        'usuario_id' (de rutero_dias, el mismo para toda la semana).
        """
        ...

    @abstractmethod
    async def eliminar_rutero_dia(self, fecha: date, asesor: str) -> bool:
        """
        Borra el rutero_dia de esa fecha+asesor (cascada a rutero_clientes;
        las novedades de esos clientes sobreviven, ver migración SET NULL).
        Retorna True si había algo que borrar.
        """
        ...
