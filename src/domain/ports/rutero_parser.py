from abc import ABC, abstractmethod
from typing import List

from src.domain.entities.cliente import Cliente


class RuteroParser(ABC):
    @abstractmethod
    def parse(self, file_bytes: bytes) -> tuple[List[Cliente], str, str]:
        """
        Parsea el archivo Excel del rutero.
        Retorna (lista_clientes, usuario_id, asesor).
        """
        ...
