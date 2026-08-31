import logging
from io import BytesIO
from typing import List, Optional, Set

import pandas as pd

from src.domain.entities.cliente import Cliente
from src.domain.ports.rutero_parser import RuteroParser

log = logging.getLogger(__name__)

# Un mismo campo interno puede tener varios nombres de columna posibles:
# el formato antiguo (RUTERO_*.xlsx) y el nuevo (ACTUALIZACION_DATOS_TV_*.xlsx,
# hoja "Informe") nombran distinto las mismas columnas. Varias claves pueden
# apuntar al mismo valor sin problema.
COLUMN_MAP = {
    # Identificador de la asesora (código de PUESTO, no de persona) —
    # antes solo "Usuario", el formato nuevo lo llama "COD ASESOR".
    "Usuario": "usuario",
    "COD ASESOR": "usuario",
    # "Asesor" (antiguo) es quien visita al cliente en CAMPO, no tiene
    # relación con "COD ASESOR"/"Usuario" (BR-016).
    "Asesor": "asesor_campo",
    "Cod Cliente": "cod_cliente",
    "Codigo": "cod_cliente",
    "Documento": "documento",
    "Cliente": "nombre",
    "Razon social": "razon_social",
    "Razon s.": "razon_social",
    "Direccion": "direccion",
    "Barrio": "barrio",
    "Ciudad": "ciudad",
    "Dias Visita": "dias_visita",
    "Dias": "dias_visita",
    "Telefono": "telefono",
    "Novedades": "novedad_excel",
    "NOVEDAD": "novedad_excel",
    # Columnas nuevas, sin equivalente en el formato antiguo.
    "OBSERVACION": "observacion_excel",
    "DATO A CORREGIR": "dato_a_corregir",
    "Email.": "email",
    "Segmento": "segmento",
    "Telefono2": "telefono2",
}

# Campos sin los cuales no se puede repartir el rutero por día ni
# identificar al cliente. Si faltan, el archivo se cargaba antes en
# silencio sin insertar nada — ahora falla con un mensaje claro.
CAMPOS_OBLIGATORIOS = ["cod_cliente", "dias_visita"]

# Nombres de columna aceptados por campo interno, solo para el mensaje de
# error (se arma invirtiendo COLUMN_MAP).
_NOMBRES_ACEPTADOS: dict[str, list[str]] = {}
for _nombre_original, _campo in COLUMN_MAP.items():
    _NOMBRES_ACEPTADOS.setdefault(_campo, []).append(_nombre_original)

# Búsqueda insensible a mayúsculas y a espacios sobrantes — el Excel real
# trae "ASESOR" en mayúsculas, que con comparación exacta no calzaba con
# la clave "Asesor" y el valor se perdía en silencio (quedaba "").
_COLUMN_MAP_NORMALIZADO = {clave.strip().lower(): valor for clave, valor in COLUMN_MAP.items()}


def _normalizar_columna(nombre) -> str:
    clave = str(nombre).strip().lower()
    return _COLUMN_MAP_NORMALIZADO.get(clave, nombre)


class ExcelRuteroParser(RuteroParser):
    def _elegir_hoja(self, file_bytes: bytes) -> tuple[pd.DataFrame, str]:
        """
        El libro puede traer varias hojas (ej. una "Hoja1" vacía sin usar).
        No se asume que la primera es la buena: se usa la primera que, tras
        normalizar sus columnas, tenga los campos obligatorios y al menos
        una fila.
        """
        excel_file = pd.ExcelFile(BytesIO(file_bytes))
        intentos: list[str] = []
        for nombre_hoja in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=nombre_hoja, dtype=str)
            df = df.rename(columns={c: _normalizar_columna(c) for c in df.columns})
            if len(df) == 0:
                continue
            faltantes = [c for c in CAMPOS_OBLIGATORIOS if c not in df.columns]
            if not faltantes:
                return df.fillna(""), nombre_hoja
            intentos.append(f"{nombre_hoja} (faltan: {', '.join(faltantes)})")

        detalle_aceptados = "; ".join(
            f"{campo}: {' / '.join(_NOMBRES_ACEPTADOS[campo])}" for campo in CAMPOS_OBLIGATORIOS
        )
        hojas_probadas = ", ".join(intentos) if intentos else "ninguna hoja tenía filas"
        raise ValueError(
            "El archivo no tiene las columnas necesarias en ninguna hoja "
            f"({hojas_probadas}). Nombres de columna aceptados por campo — {detalle_aceptados}."
        )

    def parse(self, file_bytes: bytes) -> tuple[List[Cliente], str, str, Set[str]]:
        df, hoja = self._elegir_hoja(file_bytes)
        log.info("Hoja usada del Excel: %r", hoja)

        usuario_id = df["usuario"].iloc[0] if "usuario" in df.columns and len(df) > 0 else ""
        # "ASESOR" (asesor de campo) puede variar por fila, no es un dato
        # único del archivo — a diferencia de "usuario", que sí se toma de
        # la primera fila porque es el mismo para todo el rutero.
        asesor_archivo = df["asesor_campo"].iloc[0] if "asesor_campo" in df.columns and len(df) > 0 else ""

        codigos_asesor: Set[str] = set()
        if "usuario" in df.columns:
            codigos_asesor = {str(v).strip() for v in df["usuario"] if str(v).strip()}

        total_filas = len(df)
        codigos_en_excel = [str(r.get("cod_cliente", "")).strip() for _, r in df.iterrows()]
        unicos_en_excel = len({c for c in codigos_en_excel if c})
        log.info(
            "Excel leído — filas totales: %d | cod_cliente únicos: %d | códigos de asesora: %s",
            total_filas, unicos_en_excel, sorted(codigos_asesor),
        )

        clientes: List[Cliente] = []
        for _, row in df.iterrows():
            cod = str(row.get("cod_cliente", "")).strip()
            nombre = str(row.get("nombre", "")).strip()
            if not cod or not nombre:
                continue
            clientes.append(
                Cliente(
                    cod_cliente=cod,
                    nombre=nombre,
                    documento=row.get("documento") or None,
                    razon_social=row.get("razon_social") or None,
                    direccion=row.get("direccion") or None,
                    barrio=row.get("barrio") or None,
                    ciudad=row.get("ciudad") or None,
                    dias_visita=row.get("dias_visita") or None,
                    telefono=row.get("telefono") or None,
                    novedad_excel=row.get("novedad_excel") or None,
                    asesor_campo=row.get("asesor_campo") or None,
                    email=row.get("email") or None,
                    segmento=row.get("segmento") or None,
                    telefono2=row.get("telefono2") or None,
                    observacion_excel=row.get("observacion_excel") or None,
                    dato_a_corregir=row.get("dato_a_corregir") or None,
                    cod_asesor=str(row.get("usuario", "")).strip() or None,
                )
            )

        return clientes, usuario_id, asesor_archivo, codigos_asesor
