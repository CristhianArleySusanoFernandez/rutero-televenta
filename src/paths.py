"""
Resolución de rutas independiente de si el proceso corre como script
o como ejecutable empaquetado con PyInstaller (--onedir).
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent


def base_dir() -> Path:
    """
    Carpeta de recursos empaquetados (plantillas, etc.).
    En el .exe es la carpeta interna que PyInstaller arma con --add-data;
    en desarrollo es la raíz del repositorio.
    """
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return _REPO_ROOT


def exe_dir() -> Path:
    """
    Carpeta donde vive el .exe — ahí se busca el .env (nunca dentro del
    bundle, es distinto por estación). En desarrollo es la raíz del repo.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return _REPO_ROOT
