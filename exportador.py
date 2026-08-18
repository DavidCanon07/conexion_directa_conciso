"""
exportador.py
Escribe DataFrames a .xlsx con formato legible: encabezado resaltado,
ancho de columna automatico, encabezado congelado y formato de moneda
segun el nombre del campo (mismo patron que "conexion directa").
"""

from pathlib import Path

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from utils import logger, manejar_errores


def _formatear_hoja(ws, df: pd.DataFrame):
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")

    columnas_moneda = []

    for col_idx, col_name in enumerate(df.columns, start=1):
        celda = ws.cell(row=1, column=col_idx)
        celda.fill = header_fill
        celda.font = header_font
        celda.alignment = Alignment(horizontal="center")

        largo_max = max(
            df[col_name].astype(str).map(len).max() if len(df) else 0,
            len(str(col_name)),
        )
        ws.column_dimensions[get_column_letter(col_idx)].width = min(largo_max + 3, 40)

        if "monto" in str(col_name).lower() or "valor" in str(col_name).lower():
            columnas_moneda.append(col_idx)

    ws.freeze_panes = "A2"

    for col_idx in columnas_moneda:
        for (celda,) in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=col_idx, max_col=col_idx):
            celda.number_format = "#,##0.00"


@manejar_errores
def guardar_con_formato(path: Path, hojas: dict) -> bool:
    """
    hojas: {"NombreHoja": DataFrame, ...}. Si algun DataFrame viene vacio
    (0 filas) igual se escribe la hoja con encabezados, pero se avisa en
    consola y en el log.
    """
    hojas_vacias = [nombre for nombre, df in hojas.items() if len(df) == 0]

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for nombre_hoja, contenido in hojas.items():
            contenido.to_excel(writer, sheet_name=nombre_hoja, index=False)
            ws = writer.sheets[nombre_hoja]
            _formatear_hoja(ws, contenido)

    print(f"[OK] Generado: {path}")
    for nombre_hoja in hojas_vacias:
        mensaje = f"   [!]  '{nombre_hoja}' en {path.name} quedo sin filas — revisa el filtro aplicado."
        print(mensaje)
        logger.warning(f"Hoja vacia: {nombre_hoja} en {path}")

    return True
