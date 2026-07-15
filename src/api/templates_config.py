from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="src/api/templates")


def _telefono_valido(telefono) -> bool:
    """True si el teléfono tiene al menos 7 dígitos reales."""
    if not telefono:
        return False
    solo_digitos = "".join(c for c in str(telefono) if c.isdigit())
    return len(solo_digitos) >= 7


templates.env.globals["telefono_valido"] = _telefono_valido
