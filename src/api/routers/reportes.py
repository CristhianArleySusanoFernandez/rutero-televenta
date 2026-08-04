from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from src.api.dependencies import get_asesor_actual, get_exportar_reporte
from src.application.use_cases.exportar_reporte import ExportarReporte

router = APIRouter(prefix="/reportes", tags=["reportes"])


@router.get("/exportar")
async def exportar_reporte(
    fecha: date | None = None,
    asesor: str = Depends(get_asesor_actual),
    uc: ExportarReporte = Depends(get_exportar_reporte),
):
    fecha = fecha or date.today()
    try:
        buffer = await uc.execute(fecha, asesor)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    filename = f"novedades_{fecha}.xlsx"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )
