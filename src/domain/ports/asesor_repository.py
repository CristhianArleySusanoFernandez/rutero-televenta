from abc import ABC, abstractmethod
from typing import List, Optional


class AsesorRepository(ABC):
    @abstractmethod
    async def listar_nombres(self) -> List[str]:
        """
        Nombres de asesores conocidos: los ya registrados en la tabla
        'asesores' más los que aparecen en ruteros cargados (columna
        'asesor' de rutero_dias), sin duplicados.
        """
        ...

    @abstractmethod
    async def crear_si_no_existe(self, nombre: str) -> None:
        """Registra el asesor si es la primera vez que se identifica."""
        ...

    @abstractmethod
    async def get_telefono_id(self, nombre: str) -> Optional[str]:
        ...

    @abstractmethod
    async def set_telefono_id(self, nombre: str, telefono_id: str) -> None:
        ...

    @abstractmethod
    async def get_codigo_asesor(self, nombre: str) -> Optional[str]:
        """Código de asesora (puesto) que la asesora tiene configurado, si alguno."""
        ...

    @abstractmethod
    async def set_codigo_asesor(self, nombre: str, codigo_asesor: str) -> None:
        ...
