import sys
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_PROYECTO))
sys.path.insert(0, str(RAIZ_PROYECTO / "src"))

from config import LAYOUT  # noqa: E402


def construir_linea(valores: dict, longitud_total: int = 560) -> str:
    """
    Construye una linea de archivo plano de prueba, colocando cada valor
    de `valores` (nombre_campo -> str) en su posicion exacta segun LAYOUT.
    Los campos no incluidos en `valores` quedan en blanco.
    """
    caracteres = [" "] * longitud_total
    for campo in LAYOUT:
        valor = str(valores.get(campo["nombre"], ""))
        valor = valor.ljust(campo["longitud"])[: campo["longitud"]]
        inicio = campo["inicio"] - 1
        caracteres[inicio: inicio + campo["longitud"]] = list(valor)
    return "".join(caracteres)
