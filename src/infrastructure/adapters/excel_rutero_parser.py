import logging
from io import BytesIO
from typing import List

import pandas as pd

from src.domain.entities.cliente import Cliente
from src.domain.ports.rutero_parser import RuteroParser

log = logging.getLogger(__name__)

COLUMN_MAP = {
    "Usuario": "usuario",
    "Asesor": "asesor",
    "Cod Cliente": "cod_cliente",
    "Documento": "documento",
    "Cliente": "nombre",
    "Razon social": "razon_social",
    "Direccion": "direccion",
    "Barrio": "barrio",
    "Ciudad": "ciudad",
    "Dias Visita": "dias_visita",
    "Telefono": "telefono",
    "NOVEDADS": "novedads",
}


class ExcelRuteroParser(RuteroParser):
    def parse(self, file_bytes: bytes) -> tuple[List[Cliente], str, str]:
        df = pd.read_excel(BytesIO(file_bytes), dtype=str)
        df = df.rename(columns={c: COLUMN_MAP.get(c, c) for c in df.columns})
        df = df.fillna("")

        usuario_id = df["usuario"].iloc[0] if "usuario" in df.columns and len(df) > 0 else ""
        asesor = df["asesor"].iloc[0] if "asesor" in df.columns and len(df) > 0 else ""

        total_filas = len(df)
        codigos_en_excel = [str(r.get("cod_cliente", "")).strip() for _, r in df.iterrows()]
        unicos_en_excel = len({c for c in codigos_en_excel if c})
        log.info("Excel leído — filas totales: %d | cod_cliente únicos: %d", total_filas, unicos_en_excel)

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
                )
            )

        return clientes, usuario_id, asesor
