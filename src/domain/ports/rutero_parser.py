from abc import ABC, abstractmethod
from typing import List, Set

from src.domain.entities.cliente import Cliente


class RuteroParser(ABC):
    @abstractmethod
    def parse(self, file_bytes: bytes) -> tuple[List[Cliente], str, str, Set[str]]:
        """
        Parsea el archivo Excel del rutero (formato antiguo o nuevo).
        Retorna (lista_clientes, usuario_id, asesor_campo, codigos_asesor)
        donde codigos_asesor es el conjunto de códigos de asesora (puesto)
        distintos encontrados en el archivo — vacío si el archivo no trae
        esa columna.
        """
        ...
