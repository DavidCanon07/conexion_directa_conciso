import pandas as pd

from reglas import _convertir_monto, _filtrar_ep


def _fila_base(**overrides):
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


def test_convertir_monto_divide_por_100():
    df = pd.DataFrame([_fila_base(**{"MONTO-1": "0000001464000"})])

    resultado = _convertir_monto(df)

    assert resultado.loc[0, "MONTO-1"] == 14640.00


def test_filtrar_ep_mantiene_fila_que_cumple_todas_las_condiciones():
    df = _convertir_monto(pd.DataFrame([_fila_base()]))

    resultado = _filtrar_ep(df, "0911")

    assert len(resultado) == 1


def test_filtrar_ep_excluye_por_red_logica_distinta():
    df = _convertir_monto(pd.DataFrame([_fila_base(**{"RED-LOGICA": "VISA"})]))

    resultado = _filtrar_ep(df, "0911")

    assert len(resultado) == 0


def test_filtrar_ep_excluye_indicador_nacional():
    df = _convertir_monto(pd.DataFrame([_fila_base(**{"INDICADOR INTER/NACIONAL": "N"})]))

    resultado = _filtrar_ep(df, "0911")

    assert len(resultado) == 0


def test_filtrar_ep_negativiza_reverso_0420():
    df = _convertir_monto(pd.DataFrame([_fila_base(**{"TIPO DE MENSAJE": "0420"})]))

    resultado = _filtrar_ep(df, "0911")

    assert resultado.loc[0, "MONTO-1"] == -10000.00


def test_filtrar_ep_negativiza_cod_tipo_trans_14():
    df = _convertir_monto(pd.DataFrame([_fila_base(**{"COD-TIPO-TRANS": "14"})]))

    resultado = _filtrar_ep(df, "0911")

    assert resultado.loc[0, "MONTO-1"] == -10000.00


def test_filtrar_ep_no_negativiza_cuando_no_aplica():
    df = _convertir_monto(pd.DataFrame([_fila_base()]))

    resultado = _filtrar_ep(df, "0911")

    assert resultado.loc[0, "MONTO-1"] == 10000.00
