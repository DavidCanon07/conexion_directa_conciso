"""
main.py
Menu interactivo del reporte EP (conexion directa concisa).

Flujo:
1. Seleccionar archivo(s) plano(s) — uno o varios (consolidado de fin
   de semana, igual que en "conexion directa")
2. Generar reporte: releer archivo(s), construir DataFrame base,
   aplicar reglas de negocio, generar el Excel con las 3 hojas
   ("EP <fecha>", "EP <fecha> VISA", "EFECTO CERO")
3. Salir

Cada generacion relee los archivos planos y reconstruye el DataFrame
desde cero (no se cachea entre corridas), igual que en "conexion
directa".
"""

import pandas as pd

from config import REPORTE_EP
from exportador import guardar_con_formato
from lector import construir_dataframe, leer_lineas
from reglas import generar_reporte
from utils import limpiar_pantalla, pausar
from validador import extraer_dia, seleccionar_archivos

estado = {"rutas": []}


def mostrar_menu():
    limpiar_pantalla()
    print("=" * 55)
    print(" PROCESAMIENTO DE ARCHIVO PLANO — REPORTE EP")
    print("=" * 55)
    if estado["rutas"]:
        print(f" Archivos actuales: {len(estado['rutas'])} seleccionado(s)")
        for ruta in estado["rutas"]:
            print(f"   - {ruta.name}")
    else:
        print(" Archivos actuales: (ninguno seleccionado)")
    print("-" * 55)
    print(" 1. Seleccionar archivo(s) plano(s)")
    print(" 2. Generar reporte EP")
    print(" 3. Salir")
    print("=" * 55)


def opcion_seleccionar():
    rutas = seleccionar_archivos()
    if rutas:
        estado["rutas"] = rutas
        print(f"\n{len(rutas)} archivo(s) seleccionado(s):")
        for ruta in rutas:
            print(f"   - {ruta.name}")
    pausar()


def _construir_dataframe_base():
    if not estado["rutas"]:
        print("\nPrimero selecciona uno o varios archivos (opcion 1).")
        pausar()
        return None

    partes = []
    for ruta in estado["rutas"]:
        dia = extraer_dia(ruta)
        if dia is None:
            print(f"\nNo se pudo determinar el dia para {ruta.name}. Se omite este archivo.")
            continue

        print(f"\nLeyendo archivo {ruta.name} (dia {dia})...")
        lineas = leer_lineas(ruta)
        if not lineas:
            print(f"El archivo {ruta.name} no tiene lineas para procesar. Se omite.")
            continue

        df_parcial = construir_dataframe(lineas)
        if df_parcial is None:
            print(f"No se pudo construir la tabla para {ruta.name}. Se omite.")
            continue

        df_parcial["__dia"] = dia
        partes.append(df_parcial)
        print(f"   {len(df_parcial)} filas asignadas al dia {dia}.")

    if not partes:
        print("\nNingun archivo pudo procesarse.")
        pausar()
        return None

    print("\nConstruyendo tabla base combinada...")
    df = pd.concat(partes, ignore_index=True)
    print(f"Tabla base construida: {len(df)} filas, {df['__dia'].nunique()} dia(s).")
    return df


def opcion_generar_reporte():
    df = _construir_dataframe_base()
    if df is None:
        return

    print("\nAplicando reglas de negocio...")
    hojas = generar_reporte(df)
    if hojas is None:
        pausar()
        return

    print("\nGenerando archivo Excel...")
    if not guardar_con_formato(REPORTE_EP, hojas):
        pausar()
        return

    print("\n[OK] Reporte EP generado.")
    pausar()


def main():
    acciones = {
        "1": opcion_seleccionar,
        "2": opcion_generar_reporte,
    }

    while True:
        mostrar_menu()
        opcion = input("Selecciona una opcion: ").strip()

        if opcion == "3":
            print("\nSaliendo...")
            break

        accion = acciones.get(opcion)
        if accion:
            accion()
        else:
            print("\nOpcion no valida.")
            pausar()


if __name__ == "__main__":
    main()
