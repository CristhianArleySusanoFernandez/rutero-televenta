import uuid

from src.domain.ports.llamada_repository import LlamadaRepository
from src.domain.ports.telefono_gateway import TelefonoGateway


class OrdenarLlamadaCliente:
    """
    El asesor confirma que quiere llamar al cliente actual de la cola.

    La app NO cuenta intentos: la asesora puede marcar al principal, al
    secundario, o ambos, en cualquier orden y las veces que quiera. El
    resultado (contestó / no contestó) lo sigue declarando ella con los
    botones de siempre — BR-002 no cambia.

    Flujo:
      1. Obtiene teléfonos y nombre del cliente desde el repositorio
         (no confía en datos que vengan del navegador: solo recibe una
         ETIQUETA — 'principal'/'secundario' —, nunca un número).
      2. Resuelve el número según la etiqueta y lo valida.
      3. Genera el llamada_id (UUID) — el servidor es quien lo genera (contrato §5.1).
      4. Persiste la correlación rutero_cliente ⇄ llamada_id ANTES de enviar
         la orden, para que el IDLE nunca llegue antes que la asociación.
      5. Ordena la llamada por el puerto (sin saber que es WebSocket).
    """

    def __init__(self, llamada_repo: LlamadaRepository, telefono_gateway: TelefonoGateway):
        self._repo = llamada_repo
        self._gateway = telefono_gateway

    async def execute(self, rutero_cliente_id: str, telefono_id: str, numero_a_usar: str = "principal") -> dict:
        if numero_a_usar not in ("principal", "secundario"):
            raise ValueError(f"numero_a_usar inválido: '{numero_a_usar}'")

        datos = await self._repo.get_datos_para_llamar(rutero_cliente_id)
        if numero_a_usar == "secundario":
            numero = datos.get("telefono2")
            if not self._numero_valido(numero):
                raise ValueError("El cliente no tiene un teléfono alterno válido")
        else:
            numero = datos.get("telefono")
            if not self._numero_valido(numero):
                raise ValueError(f"El cliente tiene un teléfono inválido: '{numero}'")

        llamada_id = str(uuid.uuid4())
        await self._repo.asociar_llamada_telefono(rutero_cliente_id, llamada_id)

        # Puede lanzar RuntimeError si el teléfono no está conectado/disponible.
        # En ese caso el llamada_id queda huérfano en la fila, sin efecto:
        # nunca llegará un IDLE con ese id y el siguiente intento lo sobrescribe.
        await self._gateway.ordenar_llamada(
            telefono_id=telefono_id,
            llamada_id=llamada_id,
            numero=str(numero),
            nombre_contacto=datos.get("nombre"),
        )

        return {"llamada_id": llamada_id, "numero": numero}

    @staticmethod
    def _numero_valido(telefono) -> bool:
        if not telefono:
            return False
        solo_digitos = "".join(c for c in str(telefono) if c.isdigit())
        return len(solo_digitos) >= 7
