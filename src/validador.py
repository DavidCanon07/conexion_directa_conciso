"""
validador.py
Seleccion de los archivos planos y extraccion de su dia de origen.
"""

import re
from pathlib import Path
from typing import List

from utils import manejar_errores

PATRON_DIA = re.compile(r"F(\d{2})(\d{2})(\d{2})", re.IGNORECASE)


@manejar_errores
def seleccionar_archivos() -> List[Path]:
    """
    Abre un dialogo grafico para elegir uno o varios archivos planos
    (Ctrl/Shift+clic para seleccion multiple). Si no hay entorno grafico
    disponible, pide las rutas por consola (separadas por coma).
    """
    rutas = []
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        seleccion = filedialog.askopenfilenames(
            title="Selecciona uno o varios archivos planos (.txt)",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")],
        )
        root.destroy()
        rutas = list(seleccion)
    except Exception:
        texto = input("Ingresa las rutas completas de los archivos planos (separadas por coma): ").strip()
        rutas = [r.strip() for r in texto.split(",") if r.strip()]

    if not rutas:
        print("No se selecciono ningun archivo.")
        return []

    rutas_path = []
    for ruta in rutas:
        ruta_path = Path(ruta)
        if not ruta_path.exists():
            raise FileNotFoundError(ruta_path)
        rutas_path.append(ruta_path)

    return rutas_path


@manejar_errores
def extraer_dia(ruta: Path) -> str:
    """
    Extrae el dia (2 digitos) del nombre del archivo plano, patron
    "GOF.GRB.FM14.FYYMMDD.txt". Si no calza, pregunta el dia por consola.
    """
    coincidencia = PATRON_DIA.search(ruta.stem)
    if coincidencia:
        return coincidencia.group(3)

    print(f"\n[!] No se pudo identificar el dia en el nombre del archivo: {ruta.name}")
    while True:
        dia = input(f"Ingresa el dia (1-2 digitos) que corresponde a '{ruta.name}': ").strip()
        if dia.isdigit() and 1 <= len(dia) <= 2:
            return dia.zfill(2)
        print("Valor invalido. Ingresa solo numeros (ej. 9 o 09).")
