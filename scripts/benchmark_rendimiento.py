"""
benchmark_rendimiento.py
Genera un archivo plano sintetico de ~1,000,000 filas y mide cuanto
tarda el pipeline completo (parseo + reglas de negocio) en procesarlo.
Uso: python scripts/benchmark_rendimiento.py [num_filas]
"""

import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lector import construir_dataframe  # noqa: E402
from reglas import generar_reporte  # noqa: E402
from tests.conftest import construir_linea  # noqa: E402


def _linea_aleatoria(i: int) -> str:
    return construir_linea({
        "TIPO-REGISTRO": random.choice(["01", "20", "21", "50"]),
        "RED-LOGICA": random.choice(["0911", "VISA", "VISN"]),
        "NUMERO-TARJETA": str(1000 + i % 5000),
        "FIID SPONSOR": "0013",
        "TIPO DE MENSAJE": random.choice(["0210", "0420"]),
        "COD-TIPO-TRANS": random.choice(["10", "14", "15"]),
        " CODIGO-RESP": "000",
        "MONTO-1": str(random.randint(1, 999999999)).zfill(13),
        "NUMERO -APROBACION": f"A{i % 5000:07d}",
        "INDICADOR INTER/NACIONAL": random.choice(["I", "N"]),
    })


def main():
    num_filas = int(sys.argv[1]) if len(sys.argv) > 1 else 1_000_000
    print(f"Generando {num_filas} lineas sinteticas...")
    lineas = [_linea_aleatoria(i) for i in range(num_filas)]

    inicio = time.perf_counter()
    df = construir_dataframe(lineas)
    tras_parseo = time.perf_counter()
    hojas = generar_reporte(df)
    tras_reglas = time.perf_counter()

    print(f"Parseo (construir_dataframe): {tras_parseo - inicio:.2f}s")
    print(f"Reglas de negocio (generar_reporte): {tras_reglas - tras_parseo:.2f}s")
    print(f"Total: {tras_reglas - inicio:.2f}s")
    for nombre, hoja in hojas.items():
        print(f"  {nombre}: {len(hoja)} filas")


if __name__ == "__main__":
    main()
