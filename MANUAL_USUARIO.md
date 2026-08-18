# Manual de usuario — Conexión Directa (reporte EP)

## ¿Qué hace este programa?

Toma el archivo plano diario que llega del banco con las transacciones de
tarjetas y lo convierte automáticamente en **un** reporte Excel con 3 hojas,
listo para usar: una hoja de transacciones EP, una hoja de transacciones EP
de la red VISA, y una hoja aparte con las transacciones que se anulan entre
sí ("EFECTO CERO"). Reemplaza el trabajo manual de aplicar filtros y
fórmulas en Excel sobre el archivo plano.

## Requisitos previos

- El equipo debe tener **Python instalado**, con las librerías `pandas` y
  `openpyxl` (esto lo prepara una sola vez el área de sistemas/soporte
  técnico, no es algo que deba hacer el usuario en cada uso). Sistemas
  instala estas dependencias ejecutando `pip install -r requirements.txt`
  desde la carpeta del proyecto (el archivo `requirements.txt` ya viene
  incluido y lista las versiones exactas a instalar).
- Debe tener **Microsoft Excel** (u otro programa compatible) instalado
  para poder abrir el reporte generado.
- Debe conservarse la carpeta completa del proyecto en el equipo (con
  todos sus archivos).

## Cómo se ejecuta

Hacer **doble clic en `orquestador.bat`**. No hace falta abrir una consola
ni escribir comandos: ese archivo se encarga de ubicarse en la carpeta
correcta y arrancar el programa. Al terminar (cuando se elige la opción
"Salir"), la ventana queda abierta para poder leer los últimos mensajes
antes de cerrarla.

> Si al hacer doble clic la ventana se abre y se cierra sola muy rápido,
> probablemente falta instalar Python en ese equipo — avisar a soporte
> técnico.

## El menú principal

Al abrir el programa se ve esto:

```
=======================================================
 PROCESAMIENTO DE ARCHIVO PLANO — REPORTE EP
=======================================================
 Archivos actuales: (ninguno seleccionado)
-------------------------------------------------------
 1. Seleccionar archivo(s) plano(s)
 2. Generar reporte EP
 3. Salir
=======================================================
Selecciona una opcion:
```

Una vez se seleccionan archivos, la línea "Archivos actuales" cambia y
lista cada archivo elegido debajo — es la única confirmación visual de qué
está cargado en la sesión.

**Orden de uso normal**: primero la opción **1** (siempre, incluso si se va
a repetir el proceso), luego la opción **2** para generar el reporte. Al
final, opción **3** para salir.

Si se escribe algo que no es 1, 2 o 3, aparece `Opcion no valida.` y se
vuelve al menú.

## Seleccionar el o los archivos planos (opción 1)

Al elegir la opción 1 se abre la ventana estándar de Windows para elegir
archivos, filtrada a archivos `.txt`.

- **Para elegir varios archivos a la vez**: mantener presionado **Ctrl**
  (para archivos sueltos) o **Shift** (para un rango consecutivo) mientras
  se hace clic — igual que en cualquier ventana de Windows.
- **¿Para qué sirve elegir varios?** El caso típico es consolidar el
  cierre de **fin de semana** en una sola corrida: seleccionar juntos el
  archivo del sábado, domingo y lunes (y también el martes si hubo
  festivo de por medio), en vez de procesar cada día por separado. El
  programa junta todas las transacciones en una sola tabla interna y
  produce un solo reporte con el total combinado — el reporte EP no
  separa los resultados por día, siempre entrega la vista conjunta de
  todo lo seleccionado.
- Si se cancela el diálogo sin elegir nada, el programa avisa "No se
  selecciono ningun archivo." y no cambia nada.

### Nombre esperado del archivo

El programa espera el patrón `GOF.GRB.FM14.FYYMMDD.txt` (año-mes-día, 2
dígitos cada uno), por ejemplo `GOF.GRB.FM14.F260813.txt` (archivo del día
13). De ese nombre, el programa solo usa los **2 últimos dígitos** (el día)
para etiquetar internamente las transacciones de ese archivo.

**Si el nombre del archivo no sigue ese patrón**, el programa no lo
descarta ni asume nada por su cuenta — en su lugar **pregunta el día por
consola**, archivo por archivo:

```
[!] No se pudo identificar el dia en el nombre del archivo: <nombre del archivo>
Ingresa el dia (1-2 digitos) que corresponde a '<nombre del archivo>':
```

- Se debe escribir solo el número del día (por ejemplo `9` o `09`, ambos
  son válidos).
- Si se escribe algo que no es un número o tiene más de 2 dígitos, el
  programa insiste: `Valor invalido. Ingresa solo numeros (ej. 9 o 09).` y
  vuelve a preguntar hasta recibir una respuesta válida.
- Esto pasa una vez por cada archivo cuyo nombre no calce con el patrón,
  mostrando siempre el nombre exacto del archivo en cuestión.

## El reporte que se genera

El Excel se guarda siempre en la carpeta **`salidas`** (dentro de la
carpeta del programa, se crea sola si no existe), con el nombre
`EP DD-MM-AA.xlsx`, usando la fecha **del día en que se ejecuta el
programa** (no la fecha de las transacciones). Contiene siempre estas 3
hojas:

### Hoja "EP \<fecha\>"

Transacciones que cumplen las condiciones de negocio del reporte EP para
la red "0911" (compras y reversos válidos, aprobados por el banco). Las
transacciones que son **reversos** (o que corresponden a un tipo de
transacción de reverso) quedan con su valor en **negativo**, para que al
sumar la hoja el reverso se reste automáticamente del total.

### Hoja "EP \<fecha\> VISA"

Lo mismo que la hoja anterior, pero para la red **VISA**. Antes de dejar la
hoja lista, el programa revisa si hay **transacciones que se anulan entre
sí** (ver siguiente sección) y, si encuentra alguna, las saca de esta hoja
y las traslada a la hoja "EFECTO CERO" — así esta hoja solo queda con
transacciones VISA que tienen efecto real, sin duplicar valores que ya se
cancelan.

### Hoja "EFECTO CERO"

Aquí caen las **parejas de transacciones que se anulan entre sí**: dos
filas de la hoja VISA que corresponden a la misma tarjeta y al mismo número
de aprobación, una en positivo y otra en negativo por exactamente el mismo
valor. En términos simples: es una transacción que se hizo y luego se
reversó (o viceversa), así que su efecto neto sobre el total es cero — no
suma ni resta nada al negocio, por lo que se separa a esta hoja para que no
"ensucie" ni duplique el conteo de la hoja VISA, pero queda visible y
disponible para quien necesite auditar o confirmar el cruce manualmente.

Si en una corrida no hay ninguna pareja que se anule, esta hoja se genera
igual, pero **vacía** (solo con los encabezados de columna) — no es un
error, simplemente no hubo transacciones de ese tipo en los archivos
procesados.

> El reporte EP siempre se calcula sobre **todo** lo seleccionado en la
> opción 1 (uno o varios archivos juntos) — no existe la opción de generar
> el reporte por día separado.

## Errores comunes y qué hacer

El programa **nunca se cierra solo** por un error — siempre vuelve al menú.
Todos los mensajes de error empiezan con `[!]`.

| Mensaje | Causa probable | Qué hacer |
|---|---|---|
| `[!] No se encontro el archivo: <ruta>` | El archivo plano fue movido, renombrado o borrado después de seleccionarlo | Volver a la opción 1 y elegirlo desde su ubicación actual |
| `[!] Sin permisos de acceso (¿el archivo esta abierto en Excel?): ...` | El Excel de salida ya existe y **está abierto en Excel** en ese momento | Cerrar ese Excel y volver a generar el reporte |
| `[!] Error de datos o configuracion: ...` | Algo en el contenido del archivo plano no es el esperado | Confirmar que el archivo seleccionado es el correcto; si persiste, avisar a soporte técnico |
| `[!] Ocurrio un error inesperado: ...` | Cualquier fallo no anticipado | Anotar el mensaje completo y reportarlo a soporte técnico; revisar la carpeta `logs` |
| `Opcion no valida.` | Se escribió algo fuera de 1-3 | Escribir un número del 1 al 3 |
| `Primero selecciona uno o varios archivos (opcion 1).` | Se intentó generar el reporte sin haber usado antes la opción 1 | Usar primero la opción 1 |
| `No se selecciono ningun archivo.` | Se canceló el diálogo de selección | Repetir la opción 1 y elegir uno o más archivos |
| `El archivo <nombre> no tiene lineas para procesar. Se omite.` | El archivo plano está vacío o dañado | Confirmar que es el archivo correcto y que no esté vacío |
| `No se pudo construir la tabla para <archivo>. Se omite.` | Error al interpretar las líneas de ese archivo | Verificar el formato del archivo; contactar soporte si persiste |
| `Ningun archivo pudo procesarse.` | Todos los archivos seleccionados fallaron | Revisar los mensajes previos y corregir la selección |
| `'<Hoja>' en <archivo>.xlsx quedo sin filas — revisa el filtro aplicado.` | El reporte se generó bien, pero esa hoja no tuvo transacciones que cumplieran la condición (muy normal en "EFECTO CERO" cuando no hubo parejas) | **No es un error crítico** — el Excel se genera igual, solo esa hoja queda sin filas. Confirmar que no se esperaban transacciones de ese tipo; si sí se esperaban, revisar que se seleccionó el archivo correcto |
| Pregunta por el día de un archivo | El nombre del archivo no sigue el patrón esperado | Escribir el día (1-2 dígitos) cuando se pida |

Cuando todo sale bien, se ve `[OK] Generado: <ruta del archivo>` y luego
`[OK] Reporte EP generado.`.

Cada ejecución queda registrada en un archivo de log diario
(`logs/ejecucion_YYYYMMDD.log`) — normalmente no hace falta abrirlo, pero
es útil para soporte técnico si hay que reportar un problema.

## Flujo paso a paso recomendado (consolidado de fin de semana)

1. Doble clic en `orquestador.bat`.
2. Elegir opción **1**. En el explorador de Windows, ubicar los archivos
   planos del banco y seleccionar con Ctrl+clic los de sábado, domingo y
   lunes (y martes si hubo festivo). Confirmar.
   - Si algún nombre no sigue el patrón esperado, responder en consola el
     día que corresponde cuando se pregunte.
3. Verificar en pantalla que aparecen listados todos los archivos
   esperados bajo "Archivos actuales".
4. Elegir opción **2** (Generar reporte EP) y esperar
   `[OK] Reporte EP generado.`.
5. Elegir opción **3** para salir.
6. Abrir el Excel generado en la carpeta `salidas` para revisión.
7. Revisar las 3 hojas: "EP \<fecha\>", "EP \<fecha\> VISA" y "EFECTO
   CERO". Si la hoja "EFECTO CERO" aparece marcada como "sin filas"
   durante el proceso, es normal si esa corrida no tuvo transacciones que
   se anularan entre sí — no requiere ninguna acción adicional.
