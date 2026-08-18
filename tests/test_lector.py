from pathlib import Path

from lector import construir_dataframe, leer_lineas
from tests.conftest import construir_linea


def test_leer_lineas_ignora_vacias(tmp_path):
    contenido = "linea1\n\n   \nlinea2\n"
    ruta = tmp_path / "plano.txt"
    ruta.write_text(contenido, encoding="utf-8")

    lineas = leer_lineas(ruta)

    assert lineas == ["linea1", "linea2"]


def test_construir_dataframe_extrae_campos_por_posicion():
    linea = construir_linea({
        "TIPO-REGISTRO": "01",
        "RED-LOGICA": "VISA",
        "MONTO-1": "0000001464000",
        "INDICADOR INTER/NACIONAL": "I",
    })

    df = construir_dataframe([linea])

    assert df.loc[0, "TIPO-REGISTRO"] == "01"
    assert df.loc[0, "RED-LOGICA"] == "VISA"
    assert df.loc[0, "MONTO-1"] == "0000001464000"
    assert df.loc[0, "INDICADOR INTER/NACIONAL"] == "I"
