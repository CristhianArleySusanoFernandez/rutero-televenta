import logging
import re
from datetime import date
from typing import Optional

from src.domain.entities.cambio_cliente import CambioCliente
from src.domain.entities.cliente import Cliente
from src.domain.ports.cambio_cliente_repository import CambioClienteRepository
from src.domain.ports.cliente_repository import ClienteRepository
from src.domain.servicios.fecha_colombia import hoy_colombia

log = logging.getLogger(__name__)

CAMPOS_EDITABLES = (
    "nombre", "razon_social", "direccion", "barrio", "ciudad", "telefono", "documento",
    # Campos del formato nuevo de Excel: editables aquí, pero se
    # sobrescriben con lo que traiga el Excel en la siguiente carga
    # (opción A, igual que el resto de _to_row()) — el aviso de eso vive
    # en la interfaz, no en este caso de uso.
    "email", "telefono2", "segmento", "observacion_excel", "dato_a_corregir",
)

# Nombre legible de cada campo para el registro de cambios (PARTE 2.5):
# se guarda este texto en `cambios_cliente.campo`, no el nombre técnico
# de la columna — pensado para que un jefe lo lea sin traducir.
# Único sitio donde vive este mapeo.
CAMPOS_LEGIBLES = {
    "nombre": "Nombre",
    "razon_social": "Razón social",
    "direccion": "Dirección",
    "barrio": "Barrio",
    "ciudad": "Ciudad",
    "telefono": "Teléfono",
    "documento": "Documento",
    "email": "Email",
    "telefono2": "Teléfono 2",
    "segmento": "Segmento",
    "observacion_excel": "Observación",
    "dato_a_corregir": "Dato a corregir",
}

# Validación simple, no una RFC 5322 completa: solo evita errores obvios
# de tipeo ("@" y un punto después de la arroba).
_PATRON_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class EditarCliente:
    """
    Corrige los datos de un cliente. Nunca toca cod_cliente (clave del
    upsert de rutero) ni dias_visita (determina el día de la cola,
    BR-009/BR-010) — esos campos ni siquiera se aceptan como parámetro.

    Por cada campo de CAMPOS_EDITABLES que realmente cambie (comparado ya
    normalizado, para que un espacio de más no cuente), registra una fila
    en `cambios_cliente` — insumo para un futuro reporte de solicitudes
    de corrección al ERP (ecom). Si el registro del historial falla, el
    cambio del cliente se aplica igual: la asesora nunca debe ver un
    error por esto (se registra en el log del servidor, no se propaga).
    """

    def __init__(self, cliente_repo: ClienteRepository, cambio_repo: Optional[CambioClienteRepository] = None):
        self._cliente_repo = cliente_repo
        self._cambio_repo = cambio_repo

    async def execute(self, cliente_id: str, datos: dict, asesor: Optional[str] = None) -> Cliente:
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

        cliente_anterior = await self._cliente_repo.get_by_id(cliente_id)

        cliente_actualizado = await self._cliente_repo.actualizar(cliente_id, datos_limpios)

        if cliente_anterior is not None:
            await self._registrar_cambios(cliente_id, cliente_anterior, datos_limpios, asesor)

        return cliente_actualizado

    async def _registrar_cambios(
        self, cliente_id: str, cliente_anterior: Cliente, datos_limpios: dict, asesor: Optional[str]
    ) -> None:
        if self._cambio_repo is None:
            return
        try:
            fecha: date = hoy_colombia()
            cambios = []
            for campo in CAMPOS_EDITABLES:
                anterior = self._normalizar(getattr(cliente_anterior, campo, None))
                nuevo = self._normalizar(datos_limpios.get(campo))
                if anterior == nuevo:
                    continue
                cambios.append(
                    CambioCliente(
                        cliente_id=cliente_id,
                        asesor=asesor,
                        campo=CAMPOS_LEGIBLES.get(campo, campo),
                        valor_anterior=anterior,
                        valor_nuevo=nuevo,
                        fecha=fecha,
                    )
                )
            if cambios:
                await self._cambio_repo.crear_lote(cambios)
        except Exception:
            # Nunca debe impedir que la corrección del cliente se guarde.
            log.exception("No se pudo registrar el historial de cambios del cliente %s", cliente_id)

    @staticmethod
    def _normalizar(valor) -> Optional[str]:
        if valor is None:
            return None
        texto = " ".join(str(valor).split())
        return texto or None
