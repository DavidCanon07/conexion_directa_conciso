"""
reglas.py
Reglas de negocio del reporte EP (RED-LOGICA "0911" y "VISA").

Ambas hojas comparten los mismos filtros base y la misma negativizacion
de MONTO-1; solo cambian en el valor de RED-LOGICA, y la hoja VISA
ademas retira las "parejas de efecto cero" antes del resultado final.
"""

import pandas as pd

from utils import manejar_errores

COLUMNAS_LLAVE_EFECTO_CERO = ["NUMERO-TARJETA", "NUMERO -APROBACION"]


def _convertir_monto(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "MONTO-1" in df.columns:
        # MONTO-1 viene como texto de ancho fijo (13 digitos) con 2
        # decimales implicitos en los ultimos 2 digitos.
        df["MONTO-1"] = pd.to_numeric(df["MONTO-1"], errors="coerce") / 100
    return df


def _filtrar_ep(df: pd.DataFrame, red_logica: str) -> pd.DataFrame:
    """
    Aplica los filtros base + negativizacion de MONTO-1 comunes a ambas
    hojas EP. No aplica ningun ordenamiento final; cada llamador decide
    el orden porque hoja 1 y hoja 2 terminan con criterios distintos.
    """
    cond_red = df.get("RED-LOGICA", pd.Series(dtype=str)).eq(red_logica)
    cond_tipo_reg = df.get("TIPO-REGISTRO", pd.Series(dtype=str)).isin(["01", "20", "21"])
    cond_fiid = df.get("FIID SPONSOR", pd.Series(dtype=str)).eq("0013")
    cond_msg = df.get("TIPO DE MENSAJE", pd.Series(dtype=str)).isin(["0210", "0420"])
    cond_cod_tipo = df.get("COD-TIPO-TRANS", pd.Series(dtype=str)).isin(["10", "14"])
    cond_resp = df.get(" CODIGO-RESP", pd.Series(dtype=str)).between("000", "009")
    cond_indicador = df.get("INDICADOR INTER/NACIONAL", pd.Series(dtype=str)).eq("I")

    hoja = df[
        cond_red & cond_tipo_reg & cond_fiid & cond_msg
        & cond_cod_tipo & cond_resp & cond_indicador
    ].copy()

    # Negativizacion: reversos (TIPO DE MENSAJE "0420") y transacciones
    # COD-TIPO-TRANS "14" quedan en negativo. -abs() (no negacion directa)
    # evita que una fila que cumpla ambas condiciones quede positiva otra
    # vez si se re-evalua.
    cond_negativo = (
        hoja.get("TIPO DE MENSAJE", pd.Series(dtype=str)).eq("0420")
        | hoja.get("COD-TIPO-TRANS", pd.Series(dtype=str)).eq("14")
    )
    hoja.loc[cond_negativo, "MONTO-1"] = -hoja.loc[cond_negativo, "MONTO-1"].abs()

    return hoja


def _detectar_efecto_cero(df: pd.DataFrame) -> tuple:
    """
    Identifica parejas de filas cuyo MONTO-1 se anula (una negativa y una
    positiva con la misma tarjeta, aprobacion y valor absoluto). Usa un
    numero de ocurrencia por llave (groupby().cumcount()) para emparejar
    1 a 1 incluso con llaves duplicadas, sin loops en Python — necesario
    para que archivos de hasta 1M de filas se procesen en segundos.

    Devuelve (df_restante, df_efecto_cero): el primero excluye las filas
    emparejadas, el segundo contiene ambas filas (negativa y positiva) de
    cada pareja encontrada, con las columnas originales del df de entrada.
    """
    trabajo = df.reset_index(drop=False).rename(columns={"index": "_idx_original"})
    trabajo["_abs_monto"] = trabajo["MONTO-1"].abs()

    llave = COLUMNAS_LLAVE_EFECTO_CERO + ["_abs_monto"]
    negativos = trabajo[trabajo["MONTO-1"] < 0].copy()
    positivos = trabajo[trabajo["MONTO-1"] > 0].copy()

    if negativos.empty or positivos.empty:
        return df.copy(), df.iloc[0:0].copy()

    negativos["_ocurrencia"] = negativos.groupby(llave).cumcount()
    positivos["_ocurrencia"] = positivos.groupby(llave).cumcount()

    parejas = negativos.merge(
        positivos,
        on=llave + ["_ocurrencia"],
        suffixes=("_neg", "_pos"),
    )

    if parejas.empty:
        return df.copy(), df.iloc[0:0].copy()

    indices_pareja = set(parejas["_idx_original_neg"]) | set(parejas["_idx_original_pos"])
    df_efecto_cero = df.loc[sorted(indices_pareja)].copy()
    df_restante = df.drop(index=indices_pareja).copy()
    return df_restante, df_efecto_cero


@manejar_errores
def generar_reporte(df: pd.DataFrame) -> dict:
    """
    Genera las 3 hojas del reporte EP a partir del df base. La columna
    "__dia" (si existe, por seleccion multi-archivo) no se usa para
    segregar hojas: este reporte siempre trabaja sobre el universo
    combinado de todos los archivos seleccionados, igual que
    "TIPO 50"/"TIPO 12-15" en "conexion directa".
    """
    df = df.drop(columns="__dia", errors="ignore")
    df = _convertir_monto(df)

    hoja_0911 = _filtrar_ep(df, "0911").sort_values("COD-TIPO-TRANS", kind="stable")

    hoja_visa = _filtrar_ep(df, "VISA").sort_values(
        ["NUMERO-TARJETA", "NUMERO -APROBACION", "MONTO-1"], kind="stable"
    )
    hoja_visa, efecto_cero = _detectar_efecto_cero(hoja_visa)

    fecha = pd.Timestamp.now().strftime("%d-%m-%y")
    return {
        f"EP {fecha}": hoja_0911,
        f"EP {fecha} VISA": hoja_visa,
        "EFECTO CERO": efecto_cero,
    }
