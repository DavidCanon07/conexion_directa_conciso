# conexión directa conciso

Herramienta de línea de comandos que procesa archivos planos de ancho fijo
con transacciones de tarjeta (formato bancario `GOF.GRB.FM14.FYYMMDD.txt`)
y genera un único reporte Excel ("DETALLE CTA 829") con 3 hojas: `EP
<fecha>`, `EP <fecha> VISA` y `EFECTO CERO`.

Es un proyecto hermano de **"conexión directa"** (mismo layout de archivo
plano, misma arquitectura general), pero más pequeño y enfocado: un solo
libro de Excel en vez de tres archivos independientes.

## Qué hace

1. Lee uno o varios archivos planos (selección múltiple pensada para
   consolidar un cierre de fin de semana: sábado + domingo + lunes, o +
   martes si hay festivo, en una sola corrida).
2. Extrae los 55 campos del layout de ancho fijo por posición de carácter.
3. Aplica las reglas de negocio: filtra y prepara las hojas `EP` (red
   lógica `0911`) y `EP VISA`, negativiza los montos que corresponda, y
   detecta pares de "efecto cero" en la hoja VISA (transacciones que se
   cancelan entre sí: misma tarjeta, misma aprobación, mismo monto
   absoluto, una en positivo y otra en negativo).
4. Genera un único archivo `.xlsx` con las 3 hojas, con encabezado
   resaltado, ancho de columna automático, fila de encabezado congelada y
   formato de moneda en las columnas de monto.

## Requisitos

- Python 3.9+
- Dependencias declaradas en `requirements.txt` (`pandas`, `openpyxl`,
  `pytest`):

```
pip install -r requirements.txt
```

## Uso

```
python main.py
```

En Windows también se puede ejecutar con doble clic sobre
`orquestador.bat`, que se posiciona en la carpeta del script y corre
`python main.py`.

El programa muestra un menú de texto:

1. **Seleccionar archivo(s) plano(s)** — abre un diálogo de selección
   múltiple (Ctrl/Shift+clic); si no hay entorno gráfico disponible, cae a
   un prompt de consola separado por comas.
2. **Generar reporte EP** — relee los archivos seleccionados desde disco y
   reconstruye la tabla base en cada corrida (sin caché), para que el
   reporte siempre refleje el contenido actual del archivo aunque se haya
   reemplazado a mitad de sesión.
3. **Salir**

El archivo de salida se guarda en `salidas/DETALLE CTA 829 {fecha}.xlsx`.

## Estructura del proyecto

```
main.py              punto de entrada, menú interactivo
orquestador.bat       lanzador para Windows
src/
  config.py           layout de campos (55 posiciones), rutas de salida
  lector.py            parseo del archivo plano a DataFrame (pandas.read_fwf)
  reglas.py            reglas de negocio: filtro EP/VISA, efecto cero
  exportador.py        escritura del .xlsx con formato
  validador.py          selección de archivos, extracción del día
  utils.py              manejo de errores y logging
tests/                pruebas automatizadas (pytest)
scripts/               benchmark de rendimiento
docs/
  DOCUMENTACION_TECNICA.md   layout completo, reglas exactas, benchmarks
  MANUAL_USUARIO.md           manual de usuario en español
```

## Pruebas

```
pytest tests/ -v
```

## Documentación

- [`docs/DOCUMENTACION_TECNICA.md`](docs/DOCUMENTACION_TECNICA.md) — tabla
  completa del layout, condiciones exactas de cada regla de negocio,
  explicación del algoritmo de emparejamiento de "efecto cero" y
  benchmarks de rendimiento.
- [`docs/MANUAL_USUARIO.md`](docs/MANUAL_USUARIO.md) — manual de usuario en
  español, con recorrido del menú, tabla de mensajes de error y
  explicación en lenguaje llano de qué es "efecto cero".
- [`CLAUDE.md`](CLAUDE.md) — guía técnica para trabajar en el código
  (arquitectura, convenciones, diferencias con el proyecto hermano
  "conexión directa").
