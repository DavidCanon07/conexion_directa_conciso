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


def test_efecto_cero_preserva_orden_del_llamador_con_tarjetas_intercaladas():
    # Regresion: antes, `df.loc[sorted(indices_pareja)]` reordenaba
    # `df_efecto_cero` por valor de indice, descartando el orden que
    # `generar_reporte` ya habia establecido (sort por tarjeta/aprobacion/
    # monto) antes de llamar a esta funcion. Con entrada intercalada
    # (tarjeta A, tarjeta B, tarjeta A, tarjeta B), el resultado debe
    # conservar el orden relativo original, no reagrupar por indice.
    df = pd.DataFrame([
        _fila("A", "AAA", 100.0),   # indice 0
        _fila("B", "BBB", 200.0),   # indice 1
        _fila("A", "AAA", -100.0),  # indice 2
        _fila("B", "BBB", -200.0),  # indice 3
    ])

    _, efecto_cero = _detectar_efecto_cero(df)

    assert len(efecto_cero) == 4
    # Orden esperado si se preserva el orden original de `df`: 0,1,2,3.
    # `sorted(indices_pareja)` tambien habria dado 0,1,2,3 aqui (coincide
    # con el orden de indice), asi que se usa un indice explicito no
    # ordenado para que el test realmente distinga ambos comportamientos.
    df_reordenado = df.loc[[2, 0, 3, 1]].copy()
    _, efecto_cero_reordenado = _detectar_efecto_cero(df_reordenado)

    assert list(efecto_cero_reordenado["NUMERO-TARJETA"]) == ["A", "A", "B", "B"]
    assert list(efecto_cero_reordenado["MONTO-1"]) == [-100.0, 100.0, -200.0, 200.0]
