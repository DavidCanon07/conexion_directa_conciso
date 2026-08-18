import pandas as pd

from reglas import _detectar_efecto_cero


def _fila(tarjeta, aprobacion, monto):
    return {"NUMERO-TARJETA": tarjeta, "NUMERO -APROBACION": aprobacion, "MONTO-1": monto}


def test_detecta_pareja_simple():
    df = pd.DataFrame([
        _fila("111", "AAA", -500.0),
        _fila("111", "AAA", 500.0),
    ])

    restante, efecto_cero = _detectar_efecto_cero(df)

    assert len(restante) == 0
    assert len(efecto_cero) == 2


def test_sin_pareja_no_se_retira_nada():
    df = pd.DataFrame([
        _fila("111", "AAA", -500.0),
        _fila("222", "BBB", 300.0),
    ])

    restante, efecto_cero = _detectar_efecto_cero(df)

    assert len(restante) == 2
    assert len(efecto_cero) == 0


def test_multiplicidad_empareja_1_a_1():
    df = pd.DataFrame([
        _fila("111", "AAA", -500.0),
        _fila("111", "AAA", -500.0),
        _fila("111", "AAA", 500.0),
    ])

    restante, efecto_cero = _detectar_efecto_cero(df)

    # Solo una pareja se puede formar; el segundo -500 queda sin pareja.
    assert len(restante) == 1
    assert restante.iloc[0]["MONTO-1"] == -500.0
    assert len(efecto_cero) == 2


def test_monto_cero_no_se_considera_pareja():
    df = pd.DataFrame([
        _fila("111", "AAA", 0.0),
        _fila("222", "BBB", 0.0),
    ])

    restante, efecto_cero = _detectar_efecto_cero(df)

    assert len(restante) == 2
    assert len(efecto_cero) == 0


def test_llave_distinta_tarjeta_no_empareja():
    df = pd.DataFrame([
        _fila("111", "AAA", -500.0),
        _fila("222", "AAA", 500.0),
    ])

    restante, efecto_cero = _detectar_efecto_cero(df)

    assert len(restante) == 2
    assert len(efecto_cero) == 0
