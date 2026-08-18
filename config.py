"""
config.py
Configuracion central del reporte EP.

LAYOUT reducido: solo los campos que usan las reglas de este reporte,
no los 55 campos completos del archivo plano de "conexion directa".
Cada campo se extrae por posicion absoluta (inicio/longitud), asi que
recortar la lista no afecta el parseo de los campos que si se usan.
"""

from pathlib import Path
from datetime import datetime

LAYOUT = [
    {"nombre": "TIPO-REGISTRO", "inicio": 1, "longitud": 2},
    {"nombre": "RED-LOGICA", "inicio": 3, "longitud": 4},
    {"nombre": "NUMERO-TARJETA", "inicio": 11, "longitud": 19},
    {"nombre": "FIID SPONSOR", "inicio": 34, "longitud": 4},
    {"nombre": "TIPO DE MENSAJE", "inicio": 73, "longitud": 4},
    {"nombre": "COD-TIPO-TRANS", "inicio": 179, "longitud": 2},
    {"nombre": " CODIGO-RESP", "inicio": 203, "longitud": 3},
    {"nombre": "MONTO-1", "inicio": 206, "longitud": 13},
    {"nombre": "NUMERO -APROBACION", "inicio": 279, "longitud": 8},
    {"nombre": "INDICADOR INTER/NACIONAL", "inicio": 548, "longitud": 1},
]

CARPETA_SALIDA = Path("salidas")
CARPETA_LOGS = Path("logs")
CARPETA_SALIDA.mkdir(exist_ok=True)
CARPETA_LOGS.mkdir(exist_ok=True)

ENCODING = "utf-8"

REPORTE_EP = CARPETA_SALIDA / f"EP {datetime.now().strftime('%d-%m-%y')}.xlsx"
