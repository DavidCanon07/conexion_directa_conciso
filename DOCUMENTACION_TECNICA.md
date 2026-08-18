# Documentación técnica — Conexión Directa (concisa)

Herramienta CLI de menú interactivo que procesa un archivo plano bancario de
ancho fijo (misma familia de layout que el proyecto hermano "conexión
directa") y genera **un único** reporte Excel ("EP") con 3 hojas, aplicando
reglas de negocio de filtrado, negativización y "efecto cero".

Ruta del proyecto: `c:\Users\dacanonm\OneDrive - Indra\Documentos\GitHub\conexion_directa_conciso`

## 1. Arquitectura general

Bucle de menú (`while True` en `main.py`) sin clases, con un único estado de
sesión en memoria:

```python
estado = {"rutas": [], "df": None}
```

Grafo de dependencias entre módulos:

```
main.py
 ├─ config.py      (LAYOUT reducido, REPORTE_EP)
 ├─ lector.py      (construir_dataframe, leer_lineas) → config.py, utils.py
 ├─ validador.py   (extraer_dia, seleccionar_archivos)  → utils.py
 ├─ reglas.py       (generar_reporte)                    → utils.py
 ├─ exportador.py  (guardar_con_formato)                → utils.py
 └─ utils.py       (manejar_errores, logger, limpiar_pantalla, pausar) → config.py (CARPETA_LOGS)
```

`config.py` es la base (no importa nada del proyecto). Todos los demás
módulos dependen de `utils.manejar_errores`.

Pipeline de datos, disparado por la opción 2 del menú ("Generar reporte EP"):

```
archivo(s) plano(s) .txt (ancho fijo)
        │  validador.seleccionar_archivos()   → List[Path] (diálogo Tk multi-selección)
        │  validador.extraer_dia(ruta)        → día "DD" por archivo
        ▼
lector.leer_lineas(ruta)            → líneas de texto crudas
        ▼
lector.construir_dataframe(lineas)  → DataFrame (1 fila por línea, columnas = LAYOUT, todo str)
        │  main.py: df_parcial["__dia"] = dia   (por cada archivo)
        │  pd.concat(partes, ignore_index=True) → DataFrame base combinado
        ▼
reglas.generar_reporte(df_base)     → dict {"NombreHoja": DataFrame}  (3 hojas)
        ▼
exportador.guardar_con_formato(REPORTE_EP, hojas) → .xlsx en salidas/, devuelve True/None
```

Decisiones de diseño clave:

- **Sin caché entre corridas**: cada vez que se elige "Generar reporte EP",
  `_construir_dataframe_base()` (`main.py`) relee los archivos planos desde
  disco y reconstruye el DataFrame desde cero, igual que en "conexión
  directa" — evita trabajar con datos desactualizados si el usuario
  reemplazó el archivo plano entre generaciones.
- **Un solo reporte, no tres**: a diferencia de "conexión directa" (que
  produce Archivo 1/2/3 en libros separados), este proyecto concentra todo
  en un único libro `REPORTE_EP` con 3 hojas fijas. No hay "Archivo 2" ni
  "Archivo 3" en este proyecto.
- **Ninguna de las 3 hojas se segrega por día**: aunque la selección
  múltiple de archivos (consolidado de fin de semana) sigue soportada y
  sigue etiquetando cada fila con `"__dia"`, `generar_reporte` descarta esa
  columna al inicio (`df.drop(columns="__dia", errors="ignore")`) y siempre
  trabaja sobre el universo combinado de todos los archivos seleccionados.
  No existe aquí un equivalente de `_segregar_por_dia` de "conexión
  directa".

## 2. Estructura del archivo plano de entrada (LAYOUT reducido)

Definido en `config.py` como una lista de **10 dicts** `{"nombre", "inicio",
"longitud"}` — solo los campos que usan las reglas de este reporte, no los
55 campos completos del layout de "conexión directa". `inicio` es
1-indexado (posición del carácter) y `longitud` es la cantidad de caracteres
que ocupa el campo (no una posición final). Recortar la lista de campos no
afecta el parseo de los que sí se usan, porque cada uno se extrae por su
propia posición absoluta.

Fórmula de parseo (`lector.py`, dentro de `construir_dataframe`):

```python
campo["nombre"]: linea[campo["inicio"] - 1 : campo["inicio"] - 1 + campo["longitud"]].strip()
```

Replica un `MID(texto, inicio, longitud)` de Excel. Todo se guarda como
`str` con `.strip()` — **`lector.py` no convierte tipos**; eso se hace
explícitamente en `reglas.py` (solo para `MONTO-1`).

### Los 10 campos

| # | nombre (literal en LAYOUT) | inicio | longitud |
|---|---|---|---|
| 1 | TIPO-REGISTRO | 1 | 2 |
| 2 | RED-LOGICA | 3 | 4 |
| 3 | NUMERO-TARJETA | 11 | 19 |
| 4 | FIID SPONSOR | 34 | 4 |
| 5 | TIPO DE MENSAJE | 73 | 4 |
| 6 | COD-TIPO-TRANS | 179 | 2 |
| 7 | " CODIGO-RESP" (espacio inicial literal) | 203 | 3 |
| 8 | MONTO-1 | 206 | 13 |
| 9 | NUMERO -APROBACION | 279 | 8 |
| 10 | INDICADOR INTER/NACIONAL | 548 | 1 |

### Casos especiales del LAYOUT

- **`MONTO-1`** (13 caracteres) trae 2 decimales implícitos en los últimos 2
  dígitos. La conversión ocurre una sola vez, en `_convertir_monto`:
  ```python
  df["MONTO-1"] = pd.to_numeric(df["MONTO-1"], errors="coerce") / 100
  ```
  Ejemplo: `"0000001464000"` → `14640.00`.
- **Nombres de campo con espacios inconsistentes son literales e
  intencionales** — deben citarse tal cual en el código, no normalizarse:
  `" CODIGO-RESP"` (espacio inicial) y `"NUMERO -APROBACION"` (espacio antes
  del guion).
- `leer_lineas` solo descarta líneas vacías (`if linea.strip()`); no valida
  que cada línea tenga el ancho total esperado. Una línea más corta produce
  menos caracteres o cadena vacía en los campos finales, sin lanzar error.
- `COLUMNAS_LLAVE_EFECTO_CERO = ["NUMERO-TARJETA", "NUMERO -APROBACION"]`
  (en `reglas.py`) es la única constante que reutiliza nombres de columna
  del LAYOUT fuera de `_filtrar_ep` — ver sección 4.

## 3. Selección múltiple de archivos y etiquetado por día

**`validador.seleccionar_archivos()`** abre `tkinter.filedialog.askopenfilenames`
(soporta Ctrl/Shift+clic) filtrado a `*.txt`. Si tkinter no está disponible
o falla, cae en un fallback de consola que pide rutas separadas por coma.
Valida existencia de cada ruta (`FileNotFoundError` si no) y devuelve
`List[Path]`.

**Patrón de día** — `PATRON_DIA = re.compile(r"F(\d{2})(\d{2})(\d{2})",
re.IGNORECASE)`, diseñado para `GOF.GRB.FM14.FYYMMDD.txt`. `extraer_dia(ruta)`
busca el patrón sobre `ruta.stem` con `.search()` y devuelve el **tercer
grupo capturado** (DD), descartando año y mes. Ejemplo:
`GOF.GRB.FM14.F260813.txt` → grupos `("26","08","13")` → `"13"`.

**Fallback interactivo** si el nombre no calza: imprime advertencia y entra
en un bucle pidiendo el día por consola (1-2 dígitos), validado con
`dia.isdigit() and 1 <= len(dia) <= 2` y normalizado con `.zfill(2)`. Nunca
asume un valor por defecto.

**Propagación de `__dia`**: ocurre en `main.py:_construir_dataframe_base()`,
no en `validador.py` ni `lector.py`. Por cada ruta: se extrae el día, se
leen las líneas, se construye el DataFrame parcial, se le asigna
`df_parcial["__dia"] = dia` a todas sus filas, y se acumula. Al final:
`df = pd.concat(partes, ignore_index=True)`. Si un archivo falla en
cualquier paso (día no determinable, sin líneas, error de parseo), se omite
con mensaje y se continúa con los demás.

**A diferencia de "conexión directa", `"__dia"` nunca sobrevive a
`generar_reporte`**: la primera línea de la función es
`df = df.drop(columns="__dia", errors="ignore")`. El etiquetado por día
solo existe para que, en el futuro, alguien pueda reintroducir una
segregación por día sin tener que tocar `main.py` — hoy no se usa para
nada más que ese drop defensivo (ver "Posibles mejoras").

## 4. Reglas de negocio exactas (`reglas.py`)

`generar_reporte(df)` es la única función pública del módulo, decorada con
`@manejar_errores`. Aplica, en orden:

1. `df = df.drop(columns="__dia", errors="ignore")`
2. `df = _convertir_monto(df)` — `MONTO-1` a numérico/100 (una sola vez,
   antes de filtrar; ambas hojas comparten el mismo DataFrame convertido).
3. Filtra y ordena la hoja "0911", filtra y ordena la hoja VISA, aplica
   efecto cero solo a la hoja VISA, arma el dict final con nombres de hoja
   fechados.

### `_filtrar_ep(df, red_logica)` — filtro y negativización compartidos

Ambas hojas (RED-LOGICA `"0911"` y `"VISA"`) pasan por la **misma** función,
solo cambia el valor de `red_logica`:

```python
cond_red = df.get("RED-LOGICA", pd.Series(dtype=str)).eq(red_logica)
cond_tipo_reg = df.get("TIPO-REGISTRO", pd.Series(dtype=str)).isin(["01", "20", "21"])
cond_fiid = df.get("FIID SPONSOR", pd.Series(dtype=str)).eq("0013")
cond_msg = df.get("TIPO DE MENSAJE", pd.Series(dtype=str)).isin(["0210", "0420"])
cond_cod_tipo = df.get("COD-TIPO-TRANS", pd.Series(dtype=str)).isin(["10", "14"])
cond_resp = df.get(" CODIGO-RESP", pd.Series(dtype=str)).between("000", "009")
cond_indicador = df.get("INDICADOR INTER/NACIONAL", pd.Series(dtype=str)).eq("I")

hoja = df[
    cond_red & cond_tipo_reg & cond_fiid & cond_msg
    & cond_cod_tipo & cond_resp & cond_indicador
].copy()
```

Notar, comparado con las reglas equivalentes de "conexión directa":
`TIPO-REGISTRO` acepta `["01","20","21"]` (los tres códigos juntos, no solo
`["01","20"]` ni solo `["01","21"]`), `COD-TIPO-TRANS` acepta solo
`["10","14"]` (sin `"15"`), y `INDICADOR INTER/NACIONAL` exige `"I"`
(**internacional**, no nacional) — condiciones propias de este reporte EP,
no una copia literal del otro proyecto.

**Negativización de `MONTO-1`** (dentro de la misma función, después de
filtrar): si el mensaje es un reverso (`TIPO DE MENSAJE == "0420"`) **o**
`COD-TIPO-TRANS == "14"`, el monto se fuerza a negativo:

```python
cond_negativo = (
    hoja.get("TIPO DE MENSAJE", pd.Series(dtype=str)).eq("0420")
    | hoja.get("COD-TIPO-TRANS", pd.Series(dtype=str)).eq("14")
)
hoja.loc[cond_negativo, "MONTO-1"] = -hoja.loc[cond_negativo, "MONTO-1"].abs()
```

Se usa **`-abs()`** (no una negación directa como `-hoja["MONTO-1"]`) para
que el resultado sea idempotente: una fila que ya viene negativa por venir
de un reverso, o que cumple ambas condiciones a la vez (mensaje `0420` y
`COD-TIPO-TRANS 14`), termina en negativo una sola vez y no rebota a
positivo si la expresión se reevaluara. `abs()` primero garantiza el signo
de partida sin importar el signo original del dato.

`_filtrar_ep` no ordena el resultado — el ordenamiento final queda a cargo
de `generar_reporte`, porque cada hoja usa un criterio distinto (ver abajo).

### Hoja "EP \<fecha\>" (RED-LOGICA `"0911"`)

```python
hoja_0911 = _filtrar_ep(df, "0911").sort_values("COD-TIPO-TRANS", kind="stable")
```

Orden por `COD-TIPO-TRANS`, `kind="stable"` (merge sort) para preservar el
orden relativo original en empates. No pasa por el proceso de efecto cero.

### Hoja "EP \<fecha\> VISA" (RED-LOGICA `"VISA"`)

```python
hoja_visa = _filtrar_ep(df, "VISA").sort_values(
    ["NUMERO-TARJETA", "NUMERO -APROBACION", "MONTO-1"], kind="stable"
)
hoja_visa, efecto_cero = _detectar_efecto_cero(hoja_visa)
```

Orden por tarjeta, luego aprobación, luego monto (para que las parejas de
efecto cero, si existen, queden adyacentes antes de emparejarlas), también
`kind="stable"`. **Solo esta hoja** pasa por `_detectar_efecto_cero`; su
resultado reemplaza la hoja original (parejas retiradas) y las parejas
retiradas van a la hoja separada "EFECTO CERO".

### `_detectar_efecto_cero(df)` — algoritmo de emparejamiento

Objetivo: encontrar pares de filas que representan la misma transacción
anulándose a sí misma — una con `MONTO-1` negativo y otra con el mismo valor
absoluto en positivo, sobre la **misma tarjeta y la misma aprobación** — y
sacarlas del resultado final porque su efecto neto es cero.

**Llave de emparejamiento**: `NUMERO-TARJETA` + `NUMERO -APROBACION` +
`abs(MONTO-1)` (constante `COLUMNAS_LLAVE_EFECTO_CERO + ["_abs_monto"]`).
Dos filas con la misma tarjeta, la misma aprobación y el mismo valor
absoluto de monto son candidatas a pareja, sin importar si su signo real
coincide en la práctica — lo que importa es que una esté en el lado
negativo y otra en el lado positivo.

**Por qué `groupby().cumcount()` + `merge` en vez de un loop**:

1. El DataFrame se separa en dos mitades por signo: `negativos` (`MONTO-1 <
   0`) y `positivos` (`MONTO-1 > 0`); filas en cero no participan (no hay
   "pareja" que anular si el monto ya es cero — ver `test_monto_cero_no_se_
   considera_pareja`).
2. Dentro de cada mitad, `groupby(llave).cumcount()` numera las ocurrencias
   de cada combinación de llave empezando en 0: la primera fila negativa
   con llave `(tarjeta="111", aprobacion="AAA", abs_monto=500)` recibe
   `_ocurrencia = 0`, la segunda fila negativa con esa misma llave recibe
   `_ocurrencia = 1`, y así sucesivamente — igual en el lado de positivos.
3. Un `merge` entre `negativos` y `positivos` usando `llave + ["_ocurrencia"]`
   como clave junta la ocurrencia N del lado negativo con la ocurrencia N
   del lado positivo de la misma llave. Esto da un emparejamiento **1 a 1**
   incluso cuando hay más de dos filas con la misma llave: si hay dos
   negativos y un positivo con la misma tarjeta/aprobación/monto absoluto,
   solo el negativo con `_ocurrencia = 0` encuentra pareja (el positivo con
   `_ocurrencia = 0`); el segundo negativo (`_ocurrencia = 1`) no tiene una
   fila positiva correspondiente con `_ocurrencia = 1` y el merge simplemente
   no lo incluye — queda sin pareja y permanece en el resultado final. Este
   comportamiento está cubierto explícitamente por
   `test_multiplicidad_empareja_1_a_1` en `tests/test_reglas_efecto_cero.py`.
4. Todo el emparejamiento se resuelve con operaciones vectorizadas de
   pandas (`groupby`, `cumcount`, `merge`) — sin loops en Python fila por
   fila — porque el reporte debe poder procesar archivos de hasta 1 millón
   de filas en segundos (ver sección 6, benchmark).

`_idx_original` (el índice del DataFrame de entrada, preservado con
`reset_index`) es lo que permite, después del merge, recuperar qué filas
exactas del DataFrame original quedaron emparejadas
(`indices_pareja = set(parejas["_idx_original_neg"]) | set(parejas["_idx_original_pos"])`)
y separarlas en dos resultados: `df_restante` (sin esas filas,
`.drop(index=indices_pareja)`) y `df_efecto_cero` (solo esas filas,
`.loc[sorted(indices_pareja)]`), ambos con las columnas originales del
DataFrame de entrada (las columnas auxiliares `_idx_original`,
`_abs_monto`, `_ocurrencia` nunca llegan al resultado).

Si no hay negativos o no hay positivos (`.empty`), o si el merge no produce
ninguna fila, la función devuelve `(df.copy(), df.iloc[0:0].copy())` — todo
queda en `df_restante`, nada en efecto cero.

**Por qué solo se aplica a la hoja VISA**: la anulación de parejas
(compra + reverso de la misma transacción, mismo monto en ambos signos)
es un patrón específico del flujo VISA de este reporte; la hoja "0911" no
pasa por este paso — `generar_reporte` llama a `_detectar_efecto_cero`
únicamente sobre `hoja_visa`, nunca sobre `hoja_0911`. Esto replica una
decisión de negocio confirmada para este reporte EP, no una limitación
técnica de la función (que es genérica y podría aplicarse a cualquier
DataFrame con las columnas de la llave).

### Hoja "EFECTO CERO"

Contiene, sin filtro ni orden adicional, las filas negativas y positivas de
cada pareja detectada en la hoja VISA (columnas originales, no las
auxiliares del algoritmo). Si no hubo ninguna pareja, la hoja se genera
vacía (solo encabezados) — ver manejo de hojas vacías en la sección 6.

### Nombres de hoja finales

```python
fecha = pd.Timestamp.now().strftime("%d-%m-%y")
return {
    f"EP {fecha}": hoja_0911,
    f"EP {fecha} VISA": hoja_visa,
    "EFECTO CERO": efecto_cero,
}
```

Usan la fecha del **sistema al momento de ejecutar**, no la fecha del
archivo plano ni el/los día(s) `__dia` procesados.

## 5. Manejo de errores

`utils.manejar_errores` es un decorador (`functools.wraps`) que envuelve la
función objetivo en `try/except` con 4 ramas, de más a menos específica,
todas devolviendo `None` en vez de propagar la excepción:

| Excepción | Mensaje al usuario | Log |
|---|---|---|
| `FileNotFoundError` | `[!] No se encontro el archivo: {e}` | `logger.error` |
| `PermissionError` | `[!] Sin permisos de acceso (¿el archivo esta abierto en Excel?): {e}` | `logger.error` |
| `ValueError` | `[!] Error de datos o configuracion: {e}` | `logger.error` |
| `Exception` genérico | `[!] Ocurrio un error inesperado: {e}` | `logger.exception` (traceback completo) |

Aplicado a las funciones públicas: `leer_lineas`, `construir_dataframe`,
`generar_reporte`, `guardar_con_formato`, `seleccionar_archivos`,
`extraer_dia`. Las funciones internas de `reglas.py` (`_convertir_monto`,
`_filtrar_ep`, `_detectar_efecto_cero`) no llevan el decorador — su fallo se
propaga a `generar_reporte`, que sí lo tiene.

**Señal de éxito/fracaso explícita**: `guardar_con_formato` devuelve `True`
solo si el `with pd.ExcelWriter(...)` completó sin excepción; si
`manejar_errores` capturó algo (ej. `PermissionError` por archivo abierto en
Excel), nunca llega al `return True` y el decorador devuelve `None`.
`main.py` usa `if not guardar_con_formato(REPORTE_EP, hojas)` en
`opcion_generar_reporte()` para distinguir "se guardó" de "falló
silenciosamente" y no mostrar un falso `[OK]` tras un fallo real.

## 6. Generación de Excel (`exportador.py`)

`guardar_con_formato(path, hojas)` abre un único
`pd.ExcelWriter(path, engine="openpyxl")` y, por cada entrada del dict
`hojas` (las 3 son siempre DataFrames en este proyecto — no hay hoja de
layout libre como el "Hoja1" de VALOR CINTA en "conexión directa"), escribe
con `to_excel(...)` y aplica `_formatear_hoja(ws, df)`.

**`_formatear_hoja`**: encabezado con fondo azul oscuro (`1F4E78`), fuente
blanca negrita centrada; ancho de columna automático
(`min(largo_max + 3, 40)`); `freeze_panes = "A2"`. Detección de columnas
moneda **por substring del nombre en minúsculas** (`"monto"` o `"valor"` →
formato `#,##0.00`) — en este LAYOUT reducido, solo `MONTO-1` cae en esa
regla; no hay columnas de fecha en el LAYOUT (a diferencia de "conexión
directa"), así que la rama de formato de fecha nunca se activa aquí.

**Hojas vacías**: se escriben igual (con encabezados), pero se advierte en
consola y en el log (`logger.warning`) por cada una — no aborta la
generación. Es el caso normal de "EFECTO CERO" cuando no hay ninguna pareja
en la corrida.

**Nombre del archivo de salida** (`config.py`):

```python
REPORTE_EP = CARPETA_SALIDA / f"EP {datetime.now().strftime('%d-%m-%y')}.xlsx"
```

Un único archivo, dentro de `salidas/` (creada automáticamente si no
existe), con la fecha del sistema en el nombre. `CARPETA_SALIDA` y
`CARPETA_LOGS` son relativas al directorio de trabajo — por eso
`orquestador.bat` hace `cd /d "%~dp0"` antes de invocar `python main.py`.

## 7. Dependencias externas

| Paquete | Usado en | Propósito |
|---|---|---|
| `pandas` | `main.py`, `lector.py`, `reglas.py`, `exportador.py` | DataFrame, `concat`, `to_numeric`, `groupby`, `merge`, `ExcelWriter` |
| `openpyxl` | `exportador.py` | Motor de escritura xlsx + estilos manuales |
| `tkinter` (stdlib, import opcional con fallback) | `validador.py` | Diálogo de selección múltiple de archivos |
| `pytest` (solo para desarrollo) | `tests/` | Suite de pruebas |

Resto: módulos estándar (`pathlib`, `datetime`, `re`, `typing`, `functools`,
`logging`, `os`, `random`, `time`, `sys` — los tres últimos solo en
`scripts/benchmark_rendimiento.py`). No existe `requirements.txt` ni
`pyproject.toml` en la raíz — `pandas`, `openpyxl` y `pytest` deben
instalarse manualmente en el entorno Python que ejecuta el programa
(`tkinter` viene con la instalación estándar de Python en Windows).

## 8. Pruebas automatizadas (`tests/`)

Suite de **26 pruebas** con `pytest`, sin dependencias externas de red ni
archivos fijos:

| Archivo | Pruebas | Cubre |
|---|---|---|
| `test_lector.py` | 2 | Parseo por posición del LAYOUT reducido, líneas vacías descartadas |
| `test_utils.py` | 3 | `manejar_errores` (captura de las 4 ramas de excepción, retorno `None`) |
| `test_validador.py` | 2 | `extraer_dia` (patrón `FYYMMDD` y fallback interactivo) |
| `test_reglas_filtro.py` | 7 | `_convertir_monto`, `_filtrar_ep` (cada condición del filtro y la negativización, por separado) |
| `test_reglas_efecto_cero.py` | 5 | `_detectar_efecto_cero`: pareja simple, sin pareja, multiplicidad (1 a 1 con llaves duplicadas), monto cero, llave distinta |
| `test_reglas_integracion.py` | 4 | `generar_reporte` de punta a punta: 3 hojas con los nombres esperados, separación por RED-LOGICA, retiro de parejas de efecto cero de la hoja VISA, columna `"__dia"` descartada del resultado |
| `test_exportador.py` | 2 | `guardar_con_formato`: hoja normal y hoja vacía (con advertencia) |
| `test_main_integracion.py` | 1 | Flujo completo desde un archivo plano temporal hasta un `.xlsx` de 3 hojas, incluyendo `"EFECTO CERO"` |

`tests/conftest.py` expone `construir_linea(valores, longitud_total=560)`,
un helper que construye una línea de archivo plano de prueba colocando cada
valor en su posición exacta según `LAYOUT` — reutilizado también por
`scripts/benchmark_rendimiento.py` para generar datos sintéticos.

Ejecución: `pytest tests/ -v` (o `pytest tests/ -q`) desde la raíz del
proyecto. Estado actual: **26 passed**.

## 9. Rendimiento (`scripts/benchmark_rendimiento.py`)

Genera un archivo plano sintético de N filas (por defecto 1,000,000,
parámetro opcional por línea de comandos) usando `construir_linea` con
valores aleatorios plausibles para cada campo del LAYOUT, y mide por
separado el tiempo de `construir_dataframe` (parseo) y de `generar_reporte`
(reglas de negocio).

**Resultado medido con 1,000,000 de filas**: parseo (`construir_dataframe`)
2.84s, reglas de negocio (`generar_reporte`) 2.22s, **total 5.07s**. El
tiempo total varía con la carga de la máquina en la que se ejecute (E/S en
disco, otros procesos activos, etc.), pero el pipeline completo sigue sin
usar loops en Python fila por fila en ninguna etapa (ni en el parseo por
comprensión de listas/dicts, ni en las reglas vectorizadas de pandas), lo
cual es lo que permite procesar 1 millón de filas en el orden de segundos
en vez de minutos.

## 10. Convenciones y decisiones de diseño no obvias

- **Un solo reporte con 3 hojas fijas**, no tres libros como "conexión
  directa": `"EP <fecha>"`, `"EP <fecha> VISA"`, `"EFECTO CERO"`.
- **Ninguna hoja se segrega por día**, aunque `"__dia"` se sigue
  propagando durante la construcción del DataFrame base (multi-archivo
  soportado) — se descarta explícitamente al inicio de `generar_reporte`.
- **El efecto cero solo aplica a la hoja VISA**, nunca a la hoja "0911" —
  ver sección 4.
- **`-abs()` en vez de negación directa** para la negativización de
  `MONTO-1`: garantiza idempotencia sin importar el signo original del
  dato ni cuántas condiciones de negativización cumpla la fila a la vez.
- **`kind="stable"`** en los dos `sort_values` del proyecto: preserva el
  orden relativo original de filas con el mismo criterio de orden.
- **Valores de `RED-LOGICA` hardcodeados como literales `"0911"` y
  `"VISA"`** en las dos llamadas a `_filtrar_ep` dentro de
  `generar_reporte` — no vienen de `config.py` (ver "Posibles mejoras").
- **`_filtrar_ep` usa `.get(..., pd.Series(dtype=str))`** para cada
  columna en vez de indexar directo (`df["RED-LOGICA"]`): si el DataFrame
  de entrada no trajera esa columna (por ejemplo un archivo plano con
  líneas más cortas de lo esperado), la condición se evalúa contra una
  Serie vacía en vez de lanzar `KeyError`.
- Los archivos `GOF.GRB.FM14.F260813.txt` y `GOF.GRB.FM14.F260814.txt` en
  la raíz (~130+ MB cada uno) son insumos reales de prueba manual, no se
  leen por ningún test automatizado (los tests usan `construir_linea` con
  archivos temporales pequeños).

## 11. Posibles mejoras

- **Columna `PAREJA_ID` en la hoja "EFECTO CERO"**: hoy la hoja lista las
  filas emparejadas una tras otra sin ningún identificador que agrupe
  visualmente cada pareja (negativo + positivo). Añadir una columna
  `PAREJA_ID` (por ejemplo, un número secuencial asignado durante el
  `merge` en `_detectar_efecto_cero`, antes de descartar las columnas
  auxiliares) permitiría a quien revisa el Excel confirmar de un vistazo
  qué dos filas se cancelaron entre sí, sin tener que buscar manualmente
  la tarjeta/aprobación/monto coincidente.
- **Segregación por día**, si el negocio llegara a necesitar un desglose
  "EP \<día\>" en vez de (o además de) la vista combinada actual: se
  podría reintroducir un helper equivalente a `_segregar_por_dia` de
  "conexión directa", usando la columna `"__dia"` que ya se propaga en
  `main.py` pero que hoy `generar_reporte` descarta de entrada. El cambio
  quedaría contenido en `reglas.py` sin tocar `lector.py` ni `main.py`.
- **Valores de `RED-LOGICA` configurables**: `"0911"` y `"VISA"` están
  escritos como literales directamente en las dos llamadas a
  `_filtrar_ep(df, ...)` dentro de `generar_reporte`. Si en el futuro se
  agregan más redes lógicas a este reporte (o cambian los códigos), sería
  más mantenible moverlos a constantes en `config.py` (p. ej.
  `RED_LOGICA_NACIONAL = "0911"`, `RED_LOGICA_VISA = "VISA"`) e
  importarlos en `reglas.py`, en vez de tener que editar el cuerpo de la
  función de negocio para un cambio de configuración.
- **Centralizar la conversión de `MONTO-1`**: hoy vive en una sola función
  (`_convertir_monto`), lo cual ya es más centralizado que el patrón
  repetido de "conexión directa" — se documenta aquí solo para que quede
  explícito que si se agregan más campos numéricos al LAYOUT reducido, el
  patrón a seguir es sumarlos a esa misma función en vez de duplicar
  conversiones dentro de `_filtrar_ep` o `generar_reporte`.

## Archivos del proyecto

| Archivo | Responsabilidad |
|---|---|
| `main.py` | Menú interactivo, orquestación, estado de sesión |
| `config.py` | LAYOUT reducido (10 campos), ruta de carpetas y del archivo de salida `REPORTE_EP` |
| `lector.py` | Lectura del archivo plano y construcción del DataFrame crudo (todo string) |
| `validador.py` | Selección de archivo(s) plano(s), extracción/confirmación del día |
| `reglas.py` | Reglas de negocio del reporte EP (filtro, negativización, efecto cero) |
| `exportador.py` | Escritura y formato del archivo Excel de salida |
| `utils.py` | Decorador `manejar_errores`, logging, utilidades de consola |
| `orquestador.bat` | Punto de entrada para el usuario final (doble clic) |
| `tests/` | Suite de 26 pruebas con `pytest` |
| `scripts/benchmark_rendimiento.py` | Medición de rendimiento con datos sintéticos |
| `CLAUDE.md` | Guía de orientación para agentes/desarrolladores que trabajen en el repo |
| `MANUAL_USUARIO.md` | Manual de usuario final en español |
