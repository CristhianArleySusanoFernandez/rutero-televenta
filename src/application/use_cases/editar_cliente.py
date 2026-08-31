import re

from src.domain.entities.cliente import Cliente
from src.domain.ports.cliente_repository import ClienteRepository

CAMPOS_EDITABLES = (
    "nombre", "razon_social", "direccion", "barrio", "ciudad", "telefono", "documento",
    # Campos del formato nuevo de Excel: editables aquí, pero se
    # sobrescriben con lo que traiga el Excel en la siguiente carga
    # (opción A, igual que el resto de _to_row()) — el aviso de eso vive
    # en la interfaz, no en este caso de uso.
    "email", "telefono2", "segmento", "observacion_excel", "dato_a_corregir",
)

# Validación simple, no una RFC 5322 completa: solo evita errores obvios
# de tipeo ("@" y un punto después de la arroba).
_PATRON_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class EditarCliente:
    """
    Corrige los datos de un cliente. Nunca toca cod_cliente (clave del
    upsert de rutero) ni dias_visita (determina el día de la cola,
    BR-009/BR-010) — esos campos ni siquiera se aceptan como parámetro.
    """

    def __init__(self, cliente_repo: ClienteRepository):
        self._cliente_repo = cliente_repo

    async def execute(self, cliente_id: str, datos: dict) -> Cliente:
        nombre = " ".join((datos.get("nombre") or "").split())
        if not nombre:
            raise ValueError("El nombre del cliente no puede quedar vacío")

        datos_limpios = {"nombre": nombre}
        for campo in CAMPOS_EDITABLES:
            if campo == "nombre":
                continue
            valor = datos.get(campo)
            valor_limpio = " ".join(valor.split()) if isinstance(valor, str) else valor
            datos_limpios[campo] = valor_limpio or None

        email = datos_limpios.get("email")
        if email and not _PATRON_EMAIL.match(email):
            raise ValueError(f"El email '{email}' no parece válido")

        return await self._cliente_repo.actualizar(cliente_id, datos_limpios)
