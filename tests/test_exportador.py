import openpyxl
import pandas as pd

from exportador import guardar_con_formato


def test_guardar_con_formato_crea_archivo_con_hojas_esperadas(tmp_path):
    ruta = tmp_path / "salida.xlsx"
    hojas = {
        "EP 18-08-26": pd.DataFrame({"NUMERO-TARJETA": ["111"], "MONTO-1": [500.0]}),
        "EFECTO CERO": pd.DataFrame({"NUMERO-TARJETA": [], "MONTO-1": []}),
    }

    resultado = guardar_con_formato(ruta, hojas)

    assert resultado is True
    assert ruta.exists()
    libro = openpyxl.load_workbook(ruta)
    assert set(libro.sheetnames) == {"EP 18-08-26", "EFECTO CERO"}
    assert libro["EP 18-08-26"]["A2"].value == "111"


def test_guardar_con_formato_avisa_hoja_vacia(tmp_path, capsys):
    ruta = tmp_path / "salida.xlsx"
    hojas = {"EFECTO CERO": pd.DataFrame({"NUMERO-TARJETA": []})}

    guardar_con_formato(ruta, hojas)

    salida = capsys.readouterr().out
    assert "EFECTO CERO" in salida
    assert "sin filas" in salida
