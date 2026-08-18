"""
lector.py
Lee el archivo plano y construye el DataFrame base usando el LAYOUT
reducido de config.py.
"""

from pathlib import Path

import pandas as pd

from config import ENCODING, LAYOUT
from utils import manejar_errores


@manejar_errores
def leer_lineas(ruta: Path) -> list:
    """Lee el archivo plano y devuelve las lineas no vacias, sin salto de linea."""
    with open(ruta, "r", encoding=ENCODING, errors="replace") as f:
        return [linea.rstrip("\n\r") for linea in f if linea.strip()]


@manejar_errores
def construir_dataframe(lineas: list) -> pd.DataFrame:
    """
    Recorre LAYOUT y extrae cada campo por posicion de caracter. Todo se
    trae como texto (str) y se limpia (strip); las conversiones de tipo
    se hacen explicitamente en reglas.py.
    """
    registros = []
    for linea in lineas:
        registro = {
            campo["nombre"]: linea[campo["inicio"] - 1: campo["inicio"] - 1 + campo["longitud"]].strip()
            for campo in LAYOUT
        }
        registros.append(registro)

    return pd.DataFrame(registros)
