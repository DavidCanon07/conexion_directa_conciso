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
