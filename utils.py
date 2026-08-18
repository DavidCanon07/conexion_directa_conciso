"""
utils.py
Utilidades generales: logging y decorador de manejo de errores. Ningun
fallo de usuario debe tumbar el programa; todo pasa por manejar_errores.
"""

import functools
import logging
import os
from datetime import datetime

from config import CARPETA_LOGS

logging.basicConfig(
    filename=CARPETA_LOGS / f"ejecucion_{datetime.now():%Y%m%d}.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    encoding="utf-8",
)
logger = logging.getLogger(__name__)


def manejar_errores(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            print(f"\n[!] No se encontro el archivo: {e}")
            logger.error(f"FileNotFoundError en {func.__name__}: {e}")
        except PermissionError as e:
            print(f"\n[!] Sin permisos de acceso (¿el archivo esta abierto en Excel?): {e}")
            logger.error(f"PermissionError en {func.__name__}: {e}")
        except ValueError as e:
            print(f"\n[!] Error de datos o configuracion: {e}")
            logger.error(f"ValueError en {func.__name__}: {e}")
        except Exception as e:
            print(f"\n[!] Ocurrio un error inesperado: {e}")
            logger.exception(f"Error inesperado en {func.__name__}")
        return None
    return wrapper


def limpiar_pantalla():
    os.system("cls" if os.name == "nt" else "clear")


def pausar():
    input("\nPresiona ENTER para continuar...")
