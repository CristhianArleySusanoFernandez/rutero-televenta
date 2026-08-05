from fastapi.templating import Jinja2Templates

from src.domain.servicios.dia_visita import parsear_dia_visita
from src.paths import base_dir

templates = Jinja2Templates(directory=str(base_dir() / "src" / "api" / "templates"))


def _telefono_valido(telefono) -> bool:
    """True si el teléfono tiene al menos 7 dígitos reales."""
    if not telefono:
        return False
    solo_digitos = "".join(c for c in str(telefono) if c.isdigit())
    return len(solo_digitos) >= 7


def _dia_visita_invalido(dias_visita) -> bool:
    """True si el código de 'Dias Visita' no termina en un día válido (LU..SA)."""
    return parsear_dia_visita(dias_visita) is None


templates.env.globals["telefono_valido"] = _telefono_valido
templates.env.globals["dia_visita_invalido"] = _dia_visita_invalido
