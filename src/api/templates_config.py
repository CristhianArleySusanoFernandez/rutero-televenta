from urllib.parse import quote

from fastapi.templating import Jinja2Templates

from src.domain.servicios.dia_visita import parsear_dia_visita
from src.domain.servicios.telefono_colombia import normalizar_telefono_whatsapp
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


def _link_whatsapp_no_contesto(telefono, nombre) -> str | None:
    """
    Link wa.me con un mensaje ya escrito para avisar de la llamada perdida.
    None si el teléfono no es un móvil colombiano válido — no genera enlaces rotos.
    Es puro texto: no registra nada ni depende de I/O.
    """
    numero = normalizar_telefono_whatsapp(telefono)
    if numero is None:
        return None

    saludo = f"Hola{' ' + nombre if nombre else ''}"
    mensaje = (
        f"{saludo}, le escribimos de Distribuciones Santiago De Tunja. "
        "Intentamos comunicarnos hace un momento pero no fue posible contactarle. "
        "Cuando le quede cómodo, puede devolvernos la llamada. ¡Que tenga buen día!"
    )
    return f"https://wa.me/{numero}?text={quote(mensaje)}"


templates.env.globals["telefono_valido"] = _telefono_valido
templates.env.globals["dia_visita_invalido"] = _dia_visita_invalido
templates.env.globals["normalizar_telefono_whatsapp"] = normalizar_telefono_whatsapp
templates.env.globals["link_whatsapp_no_contesto"] = _link_whatsapp_no_contesto
