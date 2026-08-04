from src.domain.ports.asesor_repository import AsesorRepository


class SeleccionarAsesor:
    def __init__(self, asesor_repo: AsesorRepository):
        self._asesor_repo = asesor_repo

    async def execute(self, nombre: str) -> None:
        nombre = nombre.strip()
        if not nombre:
            raise ValueError("El nombre del asesor no puede estar vacío")
        await self._asesor_repo.crear_si_no_existe(nombre)
