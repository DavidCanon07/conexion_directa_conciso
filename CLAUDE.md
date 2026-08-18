# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working
with code in this repository.

## What this is

A small interactive CLI tool that parses a fixed-width flat file (bank card
transaction records) and produces **one** formatted Excel report with 3
sheets. It is a sibling project to "conexión directa" (same flat-file
layout family, same overall architecture) but a smaller, more focused
report: a single workbook ("EP") instead of three separate Archivo-N
workbooks. Dependencies are declared in `requirements.txt` at the repo
root (`pandas`, `openpyxl`, and `pytest` for tests) — install with
`pip install -r requirements.txt` into whatever Python environment runs
the script. There is no `pyproject.toml`.

Two deeper reference docs live in `docs/` and are worth reading before
making non-trivial changes:
- **`docs/DOCUMENTACION_TECNICA.md`** — the full 55-field LAYOUT table
  (identical positions to the sibling project's — expanded from an earlier
  10-field reduction so output sheets carry the complete flat-file row, not
  just the fields the business rules filter on), the exact boolean
  conditions behind `_filtrar_ep` (shared by both EP sheets), the
  negativization logic, a full prose explanation of the "efecto cero"
  pairing algorithm (`groupby().cumcount()` + `merge`), the module
  dependency graph, the measured benchmark (1,000,000 rows with the full
  55-field LAYOUT: parse ~22-30s via `pandas.read_fwf`, business rules
  ~2s, Excel write ~50s via `Workbook(write_only=True)`, total ~75-90s),
  and a "Posibles mejoras" section.
- **`docs/MANUAL_USUARIO.md`** — end-user manual in Spanish (menu walkthrough,
  error messages table, recommended weekend-consolidation flow, and a
  plain-language explanation of what "EFECTO CERO" means for someone
  without a technical background).

`main.py` and `orquestador.bat` (the entry points) live at the repo root;
the six business-logic modules (`config.py`, `lector.py`, `utils.py`,
`validador.py`, `reglas.py`, `exportador.py`) live in `src/`. `main.py`
adds `src/` to `sys.path` before importing, so the internal import
statements (`from config import ...`, etc.) are unaffected by the module
files' location.

## Running

```
python main.py
```

or on Windows, double-click / run `orquestador.bat`, which `cd`s into the
script's own directory and runs `python main.py`.

The program is a text menu (see `main.py`'s `mostrar_menu()`):
1. Select one or more flat files to process (opens a Tk file dialog with
   multi-select — Ctrl/Shift+click; falls back to a comma-separated console
   prompt if no GUI is available). Multi-select exists to consolidate a
   weekend close (Saturday+Sunday+Monday, +Tuesday if there's a holiday)
   into one run.
2. Generar reporte EP
3. Salir

Option 2 always rereads the selected flat file(s) from disk and rebuilds
the DataFrame from scratch (`_construir_dataframe_base()` in `main.py`, no
caching across runs), so the report always reflects the current file
contents even if a file was swapped out mid-session — same deliberate
design as "conexión directa".

Tests: `pytest tests/ -v` from the repo root (29 tests, all passing as of
this writing — see `docs/DOCUMENTACION_TECNICA.md` section 8 for the breakdown
by file). There is no linter or build step configured.

## Architecture

Data flows in one direction through five modules, each with a single
responsibility — same shape as "conexión directa". All five (plus
`utils.py`) live in `src/`:

```
src/config.py  →  src/lector.py  →  src/reglas.py  →  src/exportador.py
   (layout)          (parse)          (filter/pair)      (write .xlsx)
```

- **`config.py`** — `LAYOUT`: the **full** 55-field fixed-width field spec,
  identical in names and positions to the sibling project's `LAYOUT`, each
  with 1-indexed start position (`inicio`) and field length (`longitud`).
  Earlier this project shipped a reduced 10-field `LAYOUT` (only the fields
  `_filtrar_ep`/`_detectar_efecto_cero` need); it was expanded back to the
  full 55 because the output sheets must carry the complete flat-file row,
  not just the fields used for filtering — `reglas.py`'s business logic
  still only reads the ~10 fields it needs (see `COLUMNAS_REQUERIDAS` in
  `reglas.py`), the other ~45 fields simply ride along unchanged from
  `lector.py` to the Excel output. Also defines `REPORTE_EP` (the single
  output path in `salidas/`, timestamped by day) and encoding.
- **`lector.py`** — extracts every `LAYOUT` field by character position
  using `pandas.read_fwf` (C-accelerated fixed-width parser, `colspecs`
  derived from `LAYOUT`, `dtype=str` to avoid losing leading zeros or
  inferring types) into one flat `pandas.DataFrame` (`construir_dataframe`).
  Replaces an earlier per-line Python loop (55 slices + `.strip()` per
  line), which became the real bottleneck once `LAYOUT` grew from 10 to 55
  fields. Every field is kept as a stripped string; no type conversion
  happens here.
- **`reglas.py`** — all business logic, exposed through a single public
  function: `generar_reporte(df)` → `{"NombreHoja": DataFrame}` with
  exactly 3 keys: `"EP <fecha>"`, `"EP <fecha> VISA"`, `"EFECTO CERO"`.
  Internally: `_convertir_monto` (MONTO-1 to numeric/100, once, shared by
  both EP sheets), `_filtrar_ep(df, red_logica)` (the filter + reversal
  negativization shared by both sheets, parameterized only by the
  `RED-LOGICA` value — `"0911"` or `"VISA"`), and
  `_detectar_efecto_cero(df)` (pairs off VISA rows whose `MONTO-1` cancels
  out — same card + same approval number + same absolute amount, one
  negative and one positive — using `groupby().cumcount()` + `merge` for
  vectorized 1:1 pairing, applied **only** to the VISA sheet, never to the
  "0911" sheet). See `docs/DOCUMENTACION_TECNICA.md` section 4 for the exact
  boolean conditions and a full prose walkthrough of the pairing algorithm.
- **`exportador.py`** — `guardar_con_formato(path, hojas)` writes a sheets
  dict to `.xlsx` via `openpyxl.Workbook(write_only=True)` unconditionally
  (all 3 sheets in this project are always DataFrames — no free-position
  "layout libre" sheet like Archivo 3's `"Hoja1"` in "conexión directa" —
  so, unlike the sibling project, there's no need to fall back to a normal
  `Workbook`). Writes each row with `ws.append()` instead of
  `DataFrame.to_excel()` (which assigns cell-by-cell — a real cost now
  that each row has 55 columns, not 10): header styling, frozen header
  row, auto column width (estimated from a sample of the first 2000 rows,
  not the full DataFrame), and currency formatting inferred from column
  name substrings (`"monto"`/`"valor"` → `#,##0.00`, covering `MONTO-1`
  and `MONTO-2` now that the full LAYOUT is in use; there's no date column
  in this project's LAYOUT, so the `"fecha"` formatting branch never
  triggers here) are all built into `WriteOnlyCell` objects *before* each
  `ws.append()`, since write-only sheets serialize a row as soon as it's
  appended and can't be edited afterward. Writes empty DataFrame sheets
  (headers only) rather than failing when a filter matches zero rows — the
  normal case for `"EFECTO CERO"` when no pair is found — and warns in
  console + log.
- **`validador.py`** — file picker (`seleccionar_archivos`, plural — Tk
  multi-select dialog with a comma-separated console fallback) and
  `extraer_dia(ruta)`, which parses the day out of the production filename
  pattern `GOF.GRB.FM14.FYYMMDD.txt` (regex `F(\d{2})(\d{2})(\d{2})`,
  keeping the day group). If a filename doesn't match, it interactively
  asks the user which day that specific file belongs to — it never guesses
  silently. Identical to "conexión directa"'s `validador.py`.
- **`utils.py`** — `manejar_errores` decorator and `logger`. Every
  I/O-facing function in the other modules is wrapped in `manejar_errores`:
  it catches `FileNotFoundError`, `PermissionError`, `ValueError`, and any
  other `Exception`, prints a Spanish user-facing message, logs to
  `logs/ejecucion_YYYYMMDD.log`, and returns `None` instead of raising — a
  single bad file/row must never crash the menu loop in `main.py`.
- **`main.py`** — the menu loop and `estado` dict (`{"rutas": [...]}`)
  holding session state — just the selected file paths; the built
  DataFrame is a local variable inside `_construir_dataframe_base()` /
  `opcion_generar_reporte()`, never stashed in `estado`, since nothing
  ever read it back from there. Orchestrates the pipeline above; contains
  no business logic itself.

## How this project differs from "conexión directa"

This project shares its architecture, module boundaries, and several
literal helper implementations (`validador.py`, `utils.py`,
`_formatear_hoja` in `exportador.py`) with the sibling "conexión directa"
project, but differs in two structural ways worth calling out explicitly:

1. **One output workbook with 3 fixed sheet names, not 3 separate
   Archivo-N outputs.** "Conexión directa" produces `ARCHIVO_1`, `ARCHIVO_2`,
   `ARCHIVO_3` as three independent `.xlsx` files from three independent
   menu options (`generar_archivo_1/2/3`). This project has a single menu
   option ("Generar reporte EP") that writes a single `REPORTE_EP` workbook
   containing `"EP <fecha>"`, `"EP <fecha> VISA"`, and `"EFECTO CERO"` —
   all three sheets always come from the same `generar_reporte(df)` call.
2. **None of the 3 sheets are split per day, even though multi-file
   selection is still supported.** `main.py`'s `_construir_dataframe_base()`
   still loops over every selected path, calls `validador.extraer_dia`, and
   tags each partial DataFrame with `"__dia"` before concatenating — the
   multi-file / weekend-consolidation flow is unchanged. But `reglas.py`
   has no equivalent of "conexión directa"'s `_segregar_por_dia`:
   `generar_reporte`'s very first line is
   `df = df.drop(columns="__dia", errors="ignore")`, so the column is
   discarded immediately and every sheet always reflects the combined
   universe of all selected files/days, never a single day. If day-level
   splitting is ever needed, see "Posibles mejoras" in
   `docs/DOCUMENTACION_TECNICA.md` for how it could be reintroduced without
   touching `lector.py` or `main.py`.

## Multi-file selection (weekend consolidation)

Mechanically identical to "conexión directa": `_construir_dataframe_base()`
in `main.py` loops over every selected path, calls `validador.extraer_dia`
to get its day, builds that file's DataFrame via the normal single-file
`lector.py` functions, tags every row of that partial DataFrame with a
`"__dia"` column, then concatenates all partial DataFrames into one
combined `df`. The only difference from the sibling project is what
happens next: here, `reglas.py` drops `"__dia"` immediately and never uses
it for sheet splitting (see previous section).

## Key conventions to preserve when editing

- **`LAYOUT` stores `inicio` (1-indexed start position) and `longitud`
  (field length in characters)** — not an end position — matching what the
  bank's flat-file spec Excel actually exposes (`MID(texto, inicio,
  longitud)`). `lector.py` computes the 0-indexed slice internally as
  `linea[inicio-1 : inicio-1+longitud]` — don't adjust indices anywhere
  else to compensate.
- **All fields come out of `lector.py` as stripped strings.** Do type
  conversion explicitly inside `reglas.py` (currently only `MONTO-1`, in
  `_convertir_monto`) — a deliberate choice to keep full control over
  real-world data quirks, not an oversight.
- **`_filtrar_ep` is shared by both EP sheets**, parameterized only by
  `red_logica` (`"0911"` vs `"VISA"`) — don't fork it into two near-copies
  when adding conditions; add a parameter or a shared branch instead.
- **`_detectar_efecto_cero` is only ever called on the VISA sheet.** It is
  a generic pairing function (works on any DataFrame with
  `NUMERO-TARJETA` + `NUMERO -APROBACION` + `MONTO-1`), but the business
  rule scoping it to VISA only is intentional — don't apply it to the
  "0911" sheet without confirming that's a real business change, not a
  "consistency" cleanup.
- **`-abs()`, not direct negation, for negativization** in `_filtrar_ep`:
  `hoja.loc[cond_negativo, "MONTO-1"] = -hoja.loc[cond_negativo, "MONTO-1"].abs()`.
  This keeps the operation idempotent regardless of the row's original
  sign or how many negativization conditions it matches at once.
- **Never let a function raise past the menu loop.** Wrap new I/O or
  user-input-facing functions in `@manejar_errores` rather than adding
  local try/except blocks, so failures log and return to the menu instead
  of crashing.
- Field names with irregular spacing in `LAYOUT` are literal and must be
  quoted exactly as-is, never normalized: `" CODIGO-RESP"` (leading
  space), `"NUMERO -APROBACION"` (space before the hyphen),
  `"NUMEROS - CUOTAS "` (trailing space), `"COMISION -  FINANCIERA -
  ADQUIRIENTE"` (double internal space).
- **`LAYOUT` carries all 55 fields but `reglas.py` only reads ~10 of
  them** (`COLUMNAS_REQUERIDAS` in `reglas.py`) — when adding a new
  business rule that needs a field not yet referenced anywhere in
  `reglas.py`, the field is already present in the parsed DataFrame (it's
  never dropped), so no `lector.py`/`config.py` change is needed, just
  reference the field name directly.
- `generar_reporte` is implemented against real business rules and real
  `LAYOUT` field names — there is no placeholder logic left. See
  `docs/DOCUMENTACION_TECNICA.md` section 4 for the exact boolean conditions.
- Large `*.txt` files at the repo root (`GOF.GRB.FM14.F260813.txt`,
  `GOF.GRB.FM14.F260814.txt` — real production naming, days 13/14) are
  sample flat-file inputs for manual testing, ~130+ MB each — don't read
  them in full; slice or `head` a few lines instead. Automated tests never
  touch these files — they build small synthetic lines with
  `tests/conftest.py`'s `construir_linea()` helper instead, which is also
  reused by `scripts/benchmark_rendimiento.py` for the 1,000,000-row
  performance benchmark.
