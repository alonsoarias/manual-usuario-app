---
name: manual-verifier
description: Activar en la fase 7 del workflow de manuales, por el comando /manual-verify, o antes de declarar un manual entregable. Skill obligatoria — sin su informe ejecutado, no se puede afirmar que el manual está terminado.
---

# Skill: manual-verifier

Fase 7 del workflow. La piedra angular de la regla 2: **evidencia antes de afirmaciones**. Esta skill se ejecuta siempre, incluso en modo rápido, y su informe completo se muestra al usuario.

## Pre-requisitos (regla 1)

Verificar que existen:

- `salida/manual.docx` (si el brief lo pidió)
- `salida/manual.pdf` (si el brief lo pidió)
- `secciones/` con los `.md` redactados
- `capturas/` con los PNG y `MANIFIESTO.md` (esquema v2: columnas `Pantalla` y `Enmascarado`)
- `01-brief.md`, `02-plan.md`, `03-inventario.md`

Si falta cualquier output esperado, marcar como `BLOQUEADO` antes de empezar los checks.

## Los 13 checks

| # | Nombre | Bloqueante |
|---|--------|------------|
| C1 | Conteo de secciones | Sí |
| C2 | Capturas embebidas | Sí |
| C3 | Tamaño DOCX y PDF | Sí |
| C4 | Páginas vs estimación | No (advertencia) |
| C5 | Coincidencia UI con inventario | No (advertencia) |
| C6 | Marcadores y placeholders | Sí |
| C7 | Tono y voz | No (advertencia) |
| C8 | DOCX abre sin error | Sí |
| C9 | PDF tiene texto seleccionable | Sí |
| C10 | TOC presente | Sí |
| C11 | Capturas de pasos accionables anotadas | Sí |
| C12 | Salidas web (HTML/Markdown) sin rutas locales ni contenido activo | Sí (N/A si el brief no pidió `formato.html` ni `formato.markdown`) |
| C13 | Datos personales | Sí |

### C1 — Conteo de secciones (bloqueante)

Comparar:

- Secciones en `02-plan.md` (excluyendo `tabla-contenido-auto`).
- Archivos `.md` en `secciones/` (excluyendo `00-INDICE.md` y `tabla-contenido-auto`).
- Encabezados nivel 1 (`# `) en el DOCX (vía `pandoc {docx} -t markdown` y conteo de `^# `).

Las tres cifras deben coincidir. Si difieren, fallo.

### C2 — Capturas embebidas (bloqueante)

Para cada captura listada en `capturas/MANIFIESTO.md`:

- Existe el PNG físico.
- Está referenciado al menos una vez en alguna sección de `secciones/`.
- Aparece embebida en el DOCX (verificable extrayendo `salida/manual.docx` que es un ZIP y contando `word/media/*.png|*.jpg|*.jpeg`).

Tres conteos coincidentes (manifiesto, referencias, embebidas).

### C3 — Tamaño DOCX y PDF (bloqueante)

| Archivo | Mínimo | Máximo |
|---------|--------|--------|
| `salida/manual.docx` | 100 KB | 30 MB |
| `salida/manual.pdf` | 0.5 MB | 50 MB |

Tamaños fuera de rango son sospechosos: por debajo, posible compilación vacía; por encima, posibles capturas sin compresión.

### C4 — Páginas vs estimación (advertencia)

Estimar páginas:

- DOCX: heurística por palabras (≈ 250 palabras/página de cuerpo). Convertir a Markdown con Pandoc, contar palabras, dividir.
- PDF: `pdfinfo {pdf} | grep Pages` si está disponible; fallback con `pdftotext` y conteo de `\f`.

Comparar contra `paginas_objetivo` del brief. Tolerancia: ±40% (fuente única: el compilador y `/manual-compile` remiten aquí). Fuera de tolerancia, advertencia (no bloqueo).

### C5 — Coincidencia UI con inventario (advertencia)

Muestra aleatoria de 10 elementos del inventario (botones, campos, mensajes con texto literal). Para cada uno, buscar en las secciones combinadas:

- Si aparece literal → match.
- Si aparece parafraseado o ausente → marca.

Reportar tasa de coincidencia. <80% = advertencia.

### C6 — Marcadores y placeholders (bloqueante)

Buscar en todas las `secciones/*.md` los patrones:

- `[TODO]`, `[VERIFICAR]`, `[XXX]`, `[FALTA]`, `[?]`
- `TBD`, `TBA`, `tbd`, `tba`
- `lorem ipsum`, `placeholder`, `xxxxx`
- Líneas que sólo contengan `...` o `…`

Cualquier coincidencia es bloqueante.

### C7 — Tono y voz (advertencia)

Muestra de 5 párrafos al azar (no listas, no tablas, no encabezados; sólo prosa de cuerpo).

Para cada párrafo, evaluar:

- ¿Está en voz activa?
- ¿En tiempo presente?
- ¿En segunda persona (o en la convención declarada)?
- ¿Sin adjetivos vacíos de la lista de bloqueo?

Reportar tasa de cumplimiento. <80% = advertencia.

Si el plugin no puede automatizar la evaluación lingüística, listar los 5 párrafos al usuario para revisión humana y marcar el check como "revisión-humana".

### C8 — DOCX abre sin error (bloqueante)

Verificar:

- `salida/manual.docx` es un ZIP válido.
- Contiene `[Content_Types].xml`, `word/document.xml`, `word/styles.xml`.
- `pandoc {docx} -t plain` ejecuta sin error y devuelve >100 caracteres.

### C9 — PDF tiene texto seleccionable (bloqueante)

Verificar:

- `pdftotext {pdf} -` devuelve >100 palabras.
- No es un PDF de imágenes escaneadas.
- No tiene contraseña ni restricciones de copia.

Si `pdftotext` no está disponible, intentar `pdfinfo` para validar que el archivo no esté corrupto y marcar el check como "verificación-parcial".

### C10 — TOC presente (bloqueante)

Verificar:

- DOCX: contiene un `w:sdt` con `w:docPartGallery="Table of Contents"`, o el primer encabezado nivel 1 está precedido por entradas tipo TOC.
- PDF: las primeras 5 páginas contienen las palabras "Contenido", "Tabla de contenido", "Índice" o equivalente del idioma del brief, **y** al menos una entrada por sección del plan.

### C11 — Capturas de pasos accionables anotadas (bloqueante)

Para cada captura listada en `02-plan.md` cuya entrada declare `anotación: recuadro|numerada-N|flecha|halo`, verificar que el PNG tiene marcas visuales del color declarado (por defecto `#ff5722` o tonalidad próxima). Estrategia automatizable:

1. Extraer el PNG de `capturas/`.
2. Cargar con Pillow y muestrear píxeles cuyo canal R esté en `[200, 255]` y G en `[60, 120]` y B en `[20, 80]` (rango aproximado del naranja-rojo de resaltado).
3. Si la cantidad de píxeles del color de resaltado es `< 0.05%` del total, marcar como **fallido** (la anotación declarada no aparece visualmente).
4. Si el plan declara `numerada-N`, además contar regiones conexas de ese color y verificar que sean `>= N`.

Adicional: para cada sección de tipo `tarea-paso-a-paso`, listar los pasos cuyo verbo es accionable (`pulse`, `haga clic`, `escriba`, `seleccione`, `marque`, `arrastre`, `tape`, `toque`) y verificar que cada uno cita en el cuerpo una captura cuya entrada en el plan tenga anotación distinta de `ninguna`.

Si el verificador no puede ejecutar Pillow, marcar el check como `verificación-parcial` y reportar el listado de capturas pendientes de revisión humana.

### C12 — Salidas web (bloqueante, N/A si no aplica)

Sólo aplica si `01-brief.md` tiene `formato.html: true` o `formato.markdown: true`. Si ninguno de los dos está en `true`, el check es **N/A** (no se ejecuta, no cuenta como fallo ni como advertencia, no bloquea el veredicto).

Si aplica, tras la fase 6 (`manual-compiler` ya debe haber producido `salida/manual.html` y/o `salida/manual.md`):

1. Ejecutar `python3 skills/manual-verifier/scripts/check_web_output.py salida/` desde la raíz del manual.
2. El script imprime una línea `ERROR: archivo: motivo` por problema y devuelve: `0` (limpio, sin rutas locales/`file:`/directorio del usuario, cada imagen o recurso resuelve, sin `<script>`/`<iframe>`/`<object>`/`<embed>`/`on*=`/`javascript:`), `1` (encontró al menos un problema; cada línea `ERROR:` del stdout va al detalle del check), `2` (uso incorrecto — ruta inexistente o directorio sin `.html` ni `.md`; tratar como fallo del check, no como N/A: si `formato.html`/`formato.markdown` es `true` el archivo correspondiente DEBE existir).
3. rc 0 → check pasa. rc 1 o 2 → check falla (bloqueante): el detalle lista cada línea `ERROR:` tal cual la imprimió el script.

No se reimplementa la lógica de detección en el verificador: el rc del script ES el resultado del check.

### C13 — Datos personales (bloqueante)

Un dato personal publicado en un manual no se puede retirar: C13 bloquea siempre que encuentre uno, en el texto o en una captura. Dos partes, las dos obligatorias:

**1. Script** — ejecutar desde la raíz del manual:

```
python3 skills/manual-verifier/scripts/check_pii.py .
```

- Texto: `secciones/*.md` y el texto de las salidas presentes en `salida/` (`manual.pdf` con `pdftotext` y `pdfinfo`, `manual.docx` leyendo su XML incluidos los metadatos de `docProps/`, `manual.html`, `manual.md`). Busca correo, teléfono (9-15 dígitos), documento de identidad (CPF, SSN, DNI/NIE con letra, y número tras «cédula / C.C. / documento / DNI / NIT / CPF / pasaporte...»), tarjeta (Luhn), IBAN (mod-97) y token/clave de API. Son los mismos patrones con que `screenshot-capturer/references/pii-masking.md` enmascara las capturas.
- Capturas: lee `PII` de cada pantalla en `03-inventario.md` y exige, para toda captura de una pantalla `PII: sí`, `Enmascarado: sí` o `excepción: <motivo>` en `capturas/MANIFIESTO.md`. También bloquea: inventario o manifiesto sin esas columnas (esquema v1), una `Pantalla` del manifiesto que no está en el inventario, un valor de `PII` que no sea `sí`/`no` (se trata como `sí`), una excepción sin motivo y un PNG de `capturas/` sin fila en el manifiesto.
- Resultado: rc 0 → esta parte pasa; rc 1 → falla (cada línea `ERROR:` va al detalle tal cual; el script abrevia el valor, `an…om`, para que `verificacion.md` no sea otra copia del dato); rc 2 → uso incorrecto, también falla. Un PDF que no se puede leer (sin `pdftotext`, archivo corrupto) es `ERROR`, no un pase.
- Las líneas `PERMITIDO:` y `EXCEPCIÓN:` se copian al detalle del check: son el rastro de cada excepción usada.

Datos que no bloquean (datos ficticios reconocidos):

| Tipo | No bloquea |
|---|---|
| Correo | dominios reservados por RFC 2606/6761: `example.com`, `example.net`, `example.org` y sus subdominios; TLD `.example`, `.test`, `.invalid`, `.localhost` |
| Teléfono | `555-0100` a `555-0199` (rango ficticio de NANP, con o sin `+1` y prefijo de área); `07700 900000-900999` y `020 7946 0000-0999` (rangos para ficción de Ofcom, Reino Unido) |
| Tarjeta | números de prueba públicos: `4111 1111 1111 1111`, `4242 4242 4242 4242`, `5555 5555 5555 4444`, `3782 822463 10005` |
| IBAN | ejemplos de documentación: `GB82 WEST 1234 5698 7654 32`, `DE89 3704 0044 0532 0130 00` |
| Cualquiera | marcadores de relleno: menos de 4 caracteres alfanuméricos distintos (`000 000 0000`, `XXXX`) |

Contactos públicos del cliente (el correo o teléfono de soporte de la sección `soporte`) se declaran uno por línea en `pii-permitidos.txt`, en la raíz del manual, con el formato `valor | motivo` (los dos obligatorios; `#` para comentarios). La coincidencia es exacta (sin espacios, guiones ni paréntesis): permitir `soporte@acme.co` no permite `ana@acme.co`. Lo crea el usuario o el PO, nunca el verificador (R4).

**2. Revisión visual** — el script comprueba la convención del manifiesto, no los píxeles: no hace OCR (no hay `tesseract` en el entorno, y un OCR fallido daría un falso pase). Por eso el verificador abre y mira cada PNG de una pantalla `PII: sí` (incluidas las de `excepción`) y cualquier otro en que sospeche datos de personas, buscando nombres, correos, teléfonos, documentos, fotos de perfil o claves que el enmascarado no tapó. Un dato real visible → C13 falla; el detalle nombra la captura y la zona («cabecera, nombre del usuario»), nunca el dato.

C13 pasa solo si el script devuelve 0 **y** la revisión visual no encuentra nada. Si no se pudo hacer la revisión visual, C13 queda como `verificación-parcial` y el veredicto no puede ser `APROBADO`.

## Salida obligatoria: `verificacion.md`

```markdown
---
fecha: "YYYY-MM-DD HH:MM"
veredicto: "APROBADO | BLOQUEADO | PENDIENTE-PASADA-COMPLETA"
ronda: 0                       # 0 = verificación inicial; N = tras la N-ésima corrección (la pasada completa de cierre hereda el N de su ronda)
alcance: completa              # completa | acotada; solo "completa" puede emitir APROBADO
total_checks: 13
checks_pasados: N
checks_advertencia: N
checks_fallidos: N
checks_na: N                   # C12 cuando el brief no pidió formato.html ni formato.markdown; no cuenta como pasado ni como fallo
---

# Informe de verificación del manual

**Veredicto:** APROBADO ✅ / BLOQUEADO ❌ / PENDIENTE-PASADA-COMPLETA ⏳

## Resumen

| # | Check | Estado | Bloqueante |
|---|-------|--------|------------|
| C1 | Conteo de secciones | ✅ / ⚠️ / ❌ | Sí |
| C2 | Capturas embebidas | ... | Sí |
| ... | ... | ... | ... |

## Detalle por check

### C1 — Conteo de secciones

**Estado:** ✅ pasa
**Detalle:**
- Plan: 22 secciones (excluyendo TOC auto)
- Archivos en secciones/: 22
- Encabezados nivel 1 en DOCX: 22

### C2 — Capturas embebidas

**Estado:** ❌ falla (bloqueante)
**Detalle:**
- Manifiesto: 28 capturas
- Referenciadas en secciones: 28
- Embebidas en DOCX: 26 ← discrepancia de 2

**Capturas faltantes en DOCX:**
- `S07-edicion-perfil.png`
- `S12-exportar-csv.png`

**Acción recomendada:** revisar la sección S07 y S12. Posible problema con el resource-path durante la compilación. Re-ejecutar fase 6.

(... un bloque por check ...)

## Advertencias no bloqueantes

(Lista resumida de lo que no detiene la entrega pero conviene revisar manualmente.)

## Recomendaciones finales

(Si APROBADO: listar la entrega. Si BLOQUEADO: indicar qué fase re-ejecutar y con qué cambios.)
```

## Reglas

### R1 — Mostrar el informe completo

El usuario ve el informe completo en pantalla, no sólo el veredicto. Cumple regla 2.

### R2 — Bloqueo significa bloqueo

Si **cualquier** check bloqueante falla, el veredicto es `BLOQUEADO`. No se puede declarar el manual entregable.

### R3 — Reproducible

Otra ejecución sobre los mismos artefactos debe producir el mismo informe (salvo C5 y C7 que muestrean al azar; reportar la semilla usada).

### R4 — Sin tocar el manual

El verificador no modifica `secciones/`, `capturas/` ni los binarios de `salida/`. Sólo lee y reporta.

## Re-verificación tras una corrección

Cuando el orquestador corrige un `BLOQUEADO` (bucle de corrección), invoca esta skill con la **ronda**, los **hallazgos abiertos** y los **archivos cambiados**. En las rondas intermedias:

- Re-ejecutar los checks que fallaron y todo check cuyos insumos estén entre los archivos cambiados (por ejemplo, cambiar una sección afecta a los checks que leen `secciones/` o el DOCX/PDF recompilado). En duda, re-ejecutar.
- Los demás checks se reportan como `heredado (ronda N)` con el estado de la ronda en que se ejecutaron por última vez; no se vuelven a correr.
- Verificar cada hallazgo previo como resuelto o no resuelto, con la misma evidencia que el check original.
- Un fallo nuevo en lo cambiado se suma a los hallazgos abiertos. Lo que no se tocó no se re-audita en esta pasada.
- El informe declara `ronda: N` y `alcance: acotada` en el frontmatter y marca los checks heredados.

Un `APROBADO` nunca sale de una pasada acotada. Si una pasada acotada no deja bloqueantes abiertos, su veredicto es `PENDIENTE-PASADA-COMPLETA` (ni `APROBADO` ni `BLOQUEADO`): el orquestador debe pedir entonces una pasada **completa** de todos los checks sin heredar nada (`alcance: completa`); solo su resultado emite `APROBADO` o `BLOQUEADO` (regla 2). Si la acotada deja bloqueantes abiertos, el veredicto es `BLOQUEADO`.

## Anti-patrones

- Marcar como APROBADO sin ejecutar los 13 checks (o sin declarar explícitamente N/A el que no aplique).
- Saltarse C8/C9/C10 porque "obviamente está bien".
- Pasar C13 con el script en verde sin haber mirado las capturas `PII: sí`.
- Copiar a `verificacion.md` el dato personal encontrado en vez de su ubicación.
- Convertir un check bloqueante en advertencia "para no parar la entrega".
- Ocultar al usuario el informe.
- Re-ejecutar sólo los checks que pasaron y omitir los que fallaron.
