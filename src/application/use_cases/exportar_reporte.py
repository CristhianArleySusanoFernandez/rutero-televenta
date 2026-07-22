from datetime import date
from io import BytesIO

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

from src.domain.ports.llamada_repository import LlamadaRepository


class ExportarReporte:
    def __init__(self, llamada_repo: LlamadaRepository):
        self._llamada_repo = llamada_repo

    async def execute(self, fecha: date) -> BytesIO:
        # Solo los que requieren una decisión (novedad, saltado, no contestó
        # tras 2 intentos) — los "Contestó" exitosos no aportan al reporte.
        problematicos = await self._llamada_repo.get_problematicos_del_dia(fecha)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"Pendientes {fecha}"

        headers = ["Cliente", "Razón Social", "Teléfono", "Estado", "Tipo Novedad", "Observación"]
        header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)

        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=h)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

        for row_idx, n in enumerate(problematicos, 2):
            ws.cell(row=row_idx, column=1, value=n.get("nombre", ""))
            ws.cell(row=row_idx, column=2, value=n.get("razon_social", ""))
            ws.cell(row=row_idx, column=3, value=n.get("telefono", ""))
            ws.cell(row=row_idx, column=4, value=n.get("estado_reporte", ""))
            ws.cell(row=row_idx, column=5, value=n.get("tipo_novedad", ""))
            ws.cell(row=row_idx, column=6, value=n.get("observacion", ""))

        for col in ws.columns:
            max_len = max((len(str(c.value or "")) for c in col), default=10)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 50)

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer
