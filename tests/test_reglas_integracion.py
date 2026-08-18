import pandas as pd
import pytest

from reglas import generar_reporte


def _fila(**overrides):
    fila = {
        "TIPO-REGISTRO": "01",
        "RED-LOGICA": "0911",
        "NUMERO-TARJETA": "1111",
        "FIID SPONSOR": "0013",
        "TIPO DE MENSAJE": "0210",
        "COD-TIPO-TRANS": "10",
        " CODIGO-RESP": "000",
        "MONTO-1": "0000001000000",
        "NUMERO -APROBACION": "AAA1",
        "INDICADOR INTER/NACIONAL": "I",
    }
    fila.update(overrides)
    return fila


def test_generar_reporte_devuelve_3_hojas_con_nombres_esperados():
    df = pd.DataFrame([_fila(), _fila(**{"RED-LOGICA": "VISA"})])

    hojas = generar_reporte(df)

    nombres = list(hojas.keys())
    assert len(nombres) == 3
    assert any(n.startswith("EP ") and n.endswith("VISA") for n in nombres)
    assert any(n.startswith("EP ") and not n.endswith("VISA") for n in nombres)
    assert "EFECTO CERO" in nombres


def test_generar_reporte_hoja_0911_separa_por_red_logica():
    df = pd.DataFrame([
        _fila(**{"RED-LOGICA": "0911"}),
        _fila(**{"RED-LOGICA": "VISA"}),
    ])

    hojas = generar_reporte(df)
    hoja_0911 = next(df_hoja for nombre, df_hoja in hojas.items() if nombre.startswith("EP ") and not nombre.endswith("VISA"))
    hoja_visa = next(df_hoja for nombre, df_hoja in hojas.items() if nombre.endswith("VISA"))

    assert len(hoja_0911) == 1
    assert len(hoja_visa) == 1


def test_generar_reporte_retira_parejas_efecto_cero_de_hoja_visa():
    df = pd.DataFrame([
        _fila(**{"RED-LOGICA": "VISA", "NUMERO-TARJETA": "1111", "NUMERO -APROBACION": "AAA1",
                  "TIPO DE MENSAJE": "0420", "MONTO-1": "0000000050000"}),  # -> -500.00
        _fila(**{"RED-LOGICA": "VISA", "NUMERO-TARJETA": "1111", "NUMERO -APROBACION": "AAA1",
                  "TIPO DE MENSAJE": "0210", "MONTO-1": "0000000050000"}),  # -> +500.00
    ])

    hojas = generar_reporte(df)
    hoja_visa = next(df_hoja for nombre, df_hoja in hojas.items() if nombre.endswith("VISA"))

    assert len(hoja_visa) == 0
    assert len(hojas["EFECTO CERO"]) == 2


def test_generar_reporte_ignora_columna_dia():
    df = pd.DataFrame([_fila()])
    df["__dia"] = "13"

    hojas = generar_reporte(df)

    for hoja in hojas.values():
        assert "__dia" not in hoja.columns


def test_generar_reporte_columna_faltante_lanza_valueerror():
    # `generar_reporte` esta decorado con @manejar_errores, que atrapa
    # cualquier ValueError y devuelve None (comportamiento correcto para
    # el flujo real via el menu). Para probar la logica de validacion en
    # si misma sin pelear con el decorador, se llama a la funcion original
    # via el atributo `__wrapped__` que `functools.wraps` deja expuesto.
    df = pd.DataFrame([_fila()]).drop(columns=["MONTO-1"])

    with pytest.raises(ValueError, match="MONTO-1"):
        generar_reporte.__wrapped__(df)


def test_generar_reporte_columna_faltante_devuelve_none_via_decorador(capsys):
    # Complemento del test anterior: confirma que, a traves de la API
    # publica (con el decorador puesto), el fallo se traduce en el mismo
    # comportamiento amigable que cualquier otro ValueError — None y un
    # mensaje "[!] Error de datos o configuracion" — en vez de un reporte
    # vacio con un falso "[OK]".
    df = pd.DataFrame([_fila()]).drop(columns=["MONTO-1"])

    resultado = generar_reporte(df)

    assert resultado is None
    assert "Error de datos o configuracion" in capsys.readouterr().out
