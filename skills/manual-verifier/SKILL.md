---
name: manual-verifier
description: Activar en la fase 7 del workflow de manuales o por el comando /manual-verify. Skill OBLIGATORIA — codifica la regla de evidencia antes de afirmaciones. Ejecuta 10 checks (C1-C10), produce verificacion.md y un veredicto APROBADO o BLOQUEADO. Sin este informe ejecutado y mostrado, no se puede declarar el manual terminado.
---

# Skill: manual-verifier

Fase 7 del workflow. La piedra angular de la regla 2: **evidencia antes de afirmaciones**. Esta skill se ejecuta siempre, incluso en modo rápido, y su informe completo se muestra al usuario.

## Pre-requisitos (regla 1)

Verificar que existen:

- `salida/manual.docx` (si el brief lo pidió)
- `salida/manual.pdf` (si el brief lo pidió)
- `secciones/` con los `.md` redactados
- `capturas/` con los PNG y `MANIFIESTO.md`
- `01-brief.md`, `02-plan.md`, `03-inventario.md`

Si falta cualquier output esperado, marcar como `BLOQUEADO` antes de empezar los checks.

## Los 10 checks

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

Comparar contra `paginas_objetivo` del brief. Tolerancia: ±40%. Fuera de tolerancia, advertencia (no bloqueo).

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

## Salida obligatoria: `verificacion.md`

```markdown
---
fecha: "YYYY-MM-DD HH:MM"
veredicto: "APROBADO | BLOQUEADO"
total_checks: 10
checks_pasados: N
checks_advertencia: N
checks_fallidos: N
---

# Informe de verificación del manual

**Veredicto:** APROBADO ✅ / BLOQUEADO ❌

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

## Anti-patrones

- Marcar como APROBADO sin ejecutar los 10 checks.
- Saltarse C8/C9/C10 porque "obviamente está bien".
- Convertir un check bloqueante en advertencia "para no parar la entrega".
- Ocultar al usuario el informe.
- Re-ejecutar sólo los checks que pasaron y omitir los que fallaron.
