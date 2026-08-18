"""
lector.py
Lee el archivo plano y construye el DataFrame base usando el LAYOUT
completo de config.py.
"""

import io
from pathlib import Path

import pandas as pd

from config import ENCODING, LAYOUT
from utils import manejar_errores

_NOMBRES_LAYOUT = [campo["nombre"] for campo in LAYOUT]
_COLSPECS_LAYOUT = [(campo["inicio"] - 1, campo["inicio"] - 1 + campo["longitud"]) for campo in LAYOUT]


@manejar_errores
def leer_lineas(ruta: Path) -> list:
    """Lee el archivo plano y devuelve las lineas no vacias, sin salto de linea."""
    with open(ruta, "r", encoding=ENCODING, errors="replace") as f:
        return [linea.rstrip("\n\r") for linea in f if linea.strip()]


@manejar_errores
def construir_dataframe(lineas: list) -> pd.DataFrame:
    """
    Extrae cada campo de LAYOUT por posicion de caracter usando el
    parser de ancho fijo de pandas (pd.read_fwf, acelerado en C) en vez
    de un bucle Python campo por campo por linea — con archivos de
    hasta 1 millon de filas y los 55 campos completos, ese bucle es un
    cuello de botella real. Mismas posiciones que el slicing manual
    (colspecs = inicio-1, inicio-1+longitud), todo como texto
    (dtype=str, sin inferencia de tipo) y con strip por campo; las
    conversiones de tipo se siguen haciendo explicitamente en reglas.py.
    """
    if not lineas:
        return pd.DataFrame(columns=_NOMBRES_LAYOUT)

    buffer = io.StringIO("\n".join(lineas))
    df = pd.read_fwf(
        buffer,
        colspecs=_COLSPECS_LAYOUT,
        names=_NOMBRES_LAYOUT,
        dtype=str,
        header=None,
    )
    df = df.fillna("")
    for nombre in _NOMBRES_LAYOUT:
        df[nombre] = df[nombre].str.strip()
    return df
