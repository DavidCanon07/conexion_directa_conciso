import openpyxl

import main
from tests.conftest import construir_linea


def _linea_0911():
    return construir_linea({
        "TIPO-REGISTRO": "01", "RED-LOGICA": "0911", "NUMERO-TARJETA": "1111",
        "FIID SPONSOR": "0013", "TIPO DE MENSAJE": "0210", "COD-TIPO-TRANS": "10",
        " CODIGO-RESP": "000", "MONTO-1": "0000001000000",
        "NUMERO -APROBACION": "AAA1", "INDICADOR INTER/NACIONAL": "I",
    })


def test_flujo_completo_genera_excel_con_3_hojas(tmp_path, monkeypatch):
    ruta = tmp_path / "GOF.GRB.FM14.F260813.txt"
    ruta.write_text(_linea_0911() + "\n", encoding="utf-8")

    main.estado["rutas"] = [ruta]
    main.estado["df"] = None

    monkeypatch.setattr("main.pausar", lambda: None)
    main.opcion_generar_reporte()

    from config import REPORTE_EP
    assert REPORTE_EP.exists()
    libro = openpyxl.load_workbook(REPORTE_EP)
    assert len(libro.sheetnames) == 3
    assert "EFECTO CERO" in libro.sheetnames
