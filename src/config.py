"""
config.py
Configuracion central del reporte EP.

LAYOUT completo (55 campos, identico en posiciones al de "conexion
directa"): el reporte EP filtra y ordena usando solo un subconjunto de
estos campos (ver reglas.py), pero las hojas de salida deben conservar
la linea completa del archivo plano, no solo los campos usados por las
reglas de negocio. Cada campo se extrae por posicion absoluta
(inicio/longitud).
"""

from pathlib import Path
from datetime import datetime

LAYOUT = [
    {"nombre": "TIPO-REGISTRO", "inicio": 1, "longitud": 2},
    {"nombre": "RED-LOGICA", "inicio": 3, "longitud": 4},
    {"nombre": "FIID-AUTORIZA", "inicio": 7, "longitud": 4},
    {"nombre": "NUMERO-TARJETA", "inicio": 11, "longitud": 19},
    {"nombre": "RED-LOGICA-ALMACEN", "inicio": 30, "longitud": 4},
    {"nombre": "FIID SPONSOR", "inicio": 34, "longitud": 4},
    {"nombre": "CODIGO ALMACEN", "inicio": 38, "longitud": 19},
    {"nombre": "CODIGO DATAFONO", "inicio": 57, "longitud": 16},
    {"nombre": "TIPO DE MENSAJE", "inicio": 73, "longitud": 4},
    {"nombre": "ORIGINA", "inicio": 77, "longitud": 1},
    {"nombre": "RESPONDE", "inicio": 78, "longitud": 1},
    {"nombre": "FECHA-TRANSACCION", "inicio": 79, "longitud": 8},
    {"nombre": "HORA TRANSACCION", "inicio": 87, "longitud": 8},
    {"nombre": "FECHA-POSTEO", "inicio": 95, "longitud": 8},
    {"nombre": "NUMERO-SECUENCIA", "inicio": 103, "longitud": 12},
    {"nombre": "UBICACIÓN DATAFONO", "inicio": 115, "longitud": 25},
    {"nombre": "NOMBRE-ALMACEN", "inicio": 140, "longitud": 22},
    {"nombre": "CIUDAD", "inicio": 162, "longitud": 13},
    {"nombre": "DEPARTAMENTO", "inicio": 175, "longitud": 2},
    {"nombre": "PAIS", "inicio": 177, "longitud": 2},
    {"nombre": "COD-TIPO-TRANS", "inicio": 179, "longitud": 2},
    {"nombre": "COD-TIPO-TARJETA", "inicio": 181, "longitud": 1},
    {"nombre": "COD-TIPO-CTA", "inicio": 182, "longitud": 2},
    {"nombre": "NUMERO - CUENTA", "inicio": 184, "longitud": 19},
    {"nombre": " CODIGO-RESP", "inicio": 203, "longitud": 3},
    {"nombre": "MONTO-1", "inicio": 206, "longitud": 13},
    {"nombre": "MONTO-2", "inicio": 219, "longitud": 13},
    {"nombre": "FECHA-VENCE-TARJETA", "inicio": 232, "longitud": 6},
    {"nombre": "CODIGO-EMPRESA-PSP", "inicio": 238, "longitud": 4},
    {"nombre": "NUMERO-FACTURA-PSP", "inicio": 242, "longitud": 30},
    {"nombre": "ORIGEN-PSP", "inicio": 272, "longitud": 1},
    {"nombre": "NUMERO-SEGUIMIENTO", "inicio": 273, "longitud": 6},
    {"nombre": "NUMERO -APROBACION", "inicio": 279, "longitud": 8},
    {"nombre": "DRAFT-CAPTURE-FLAG", "inicio": 287, "longitud": 1},
    {"nombre": "CODIGO- REVERSO", "inicio": 288, "longitud": 2},
    {"nombre": "MONEDA", "inicio": 290, "longitud": 3},
    {"nombre": "NUMEROS - CUOTAS ", "inicio": 293, "longitud": 2},
    {"nombre": "COMISION - FCERA", "inicio": 295, "longitud": 8},
    {"nombre": "COMISION-ADMIN", "inicio": 303, "longitud": 4},
    {"nombre": "POR-RETENCION", "inicio": 307, "longitud": 4},
    {"nombre": "POR- BASE-RETENCION", "inicio": 311, "longitud": 4},
    {"nombre": "LIQUIDA-RETENCION", "inicio": 315, "longitud": 10},
    {"nombre": "COMISION - FINANCIERA - AUTORIZADOR", "inicio": 325, "longitud": 8},
    {"nombre": "COMISION -  FINANCIERA - ADQUIRIENTE", "inicio": 333, "longitud": 8},
    {"nombre": "LIQUIDA-IVA", "inicio": 341, "longitud": 12},
    {"nombre": "MODO-INGRESO-POS", "inicio": 353, "longitud": 3},
    {"nombre": "CODIGO-DE-SERVICIO-TARJETA", "inicio": 356, "longitud": 3},
    {"nombre": "POR-RETEICA", "inicio": 359, "longitud": 6},
    {"nombre": "LIQUIDA-RETEICA", "inicio": 365, "longitud": 10},
    {"nombre": "FILLER-1", "inicio": 375, "longitud": 26},
    {"nombre": "NTLF-COMISION-FIN-EMP-ADICIONAL", "inicio": 401, "longitud": 8},
    {"nombre": "FILLER-2", "inicio": 409, "longitud": 14},
    {"nombre": "PLANO", "inicio": 423, "longitud": 125},
    # Posiciones fijas fuera del bloque contiguo por spec del banco;
    # DISPOSITIVO cae dentro del rango de PLANO — es intencional, no un
    # error de layout (igual que en "conexion directa").
    {"nombre": "INDICADOR INTER/NACIONAL", "inicio": 548, "longitud": 1},
    {"nombre": "DISPOSITIVO", "inicio": 519, "longitud": 2},
]

CARPETA_SALIDA = Path("salidas")
CARPETA_LOGS = Path("logs")
CARPETA_SALIDA.mkdir(exist_ok=True)
CARPETA_LOGS.mkdir(exist_ok=True)

ENCODING = "utf-8"

REPORTE_EP = CARPETA_SALIDA / f"EP {datetime.now().strftime('%d-%m-%y')}.xlsx"
