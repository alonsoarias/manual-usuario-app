---
name: manual-compiler
description: Activar en la fase 6 del workflow de manuales o por el comando /manual-compile. Compila las secciones redactadas a DOCX (vía Pandoc) y PDF (Typst preferido, Pandoc+LaTeX como fallback). Requiere secciones/ completo y capturas/ presente. Inyecta tabla de contenido automática, numeración y, opcionalmente, plantilla DOCX del cliente con membrete.
---

# Skill: manual-compiler

Fase 6 del workflow. La única fase que produce binarios. Conecta el plugin con Pandoc, Typst y LaTeX para generar `salida/manual.docx` y `salida/manual.pdf` listos para entrega.

## Pre-requisito (regla 1)

Verificar que existen:

- `secciones/` con al menos una sección por cada ID del plan (excepto `tabla-contenido-auto`, que se genera).
- `secciones/00-INDICE.md` con orden explícito.
- `capturas/MANIFIESTO.md` con todas las capturas referenciadas en las secciones.
- `01-brief.md`, `02-plan.md`, `03-inventario.md`.

Si falta cualquiera, **abortar** y devolver a la fase pendiente.

## Dependencias del entorno

| Dependencia | Para qué | Cómo verificar |
|-------------|----------|----------------|
| `pandoc` | DOCX, conversión Markdown→Typst | `pandoc --version` |
| `python3` (≥3.8) | Concatenador, post-proceso de imágenes | `python3 --version` |
| `python3` + `Pillow` | Anotaciones y validación de imágenes | `python3 -c "import PIL"` |
| `typst` | PDF preferido | `typst --version` |
| `xelatex` o `pdflatex` | PDF de fallback | `xelatex --version` |
| Fuentes DejaVu Sans | Plantilla por defecto | en sistema |

Si falta Pandoc, abortar (es obligatorio). Si falta Typst y LaTeX, advertir y compilar sólo DOCX.

## Workflow de compilación

1. Leer `secciones/00-INDICE.md` para conocer el orden estricto.
2. Concatenar las secciones en un único Markdown intermedio (`/tmp/manual-{slug}-concat.md`) con `concatenate.py`.
3. Inyectar metadatos del brief (título, versión, fecha, idioma, autor) como YAML frontmatter para Pandoc.
4. Compilar DOCX con `compile_docx.sh`.
5. Compilar PDF con `compile_pdf.sh`.
6. Validar tamaños y contenido.
7. Mover los binarios a `salida/`.
8. Limpiar archivos intermedios.

## Compilación DOCX

Comando final (lo dispara `compile_docx.sh`):

```
pandoc {concat.md} \
  -o salida/manual.docx \
  --toc --toc-depth=3 \
  --number-sections \
  --highlight-style=tango \
  --resource-path=. \
  [--reference-doc={ruta-plantilla-cliente}.docx]
```

### Plantilla del cliente

Si el brief declara `formato.reference_doc_path`, pasar ese archivo a `--reference-doc`. Pandoc heredará:

- Estilos de párrafo y caracter (incluyendo encabezados).
- Márgenes y orientación.
- Encabezados/pies de página (con membrete).
- Numeración del documento.

Si la plantilla no existe en la ruta declarada, advertir y compilar sin ella.

## Compilación PDF

Estrategia en cascada (lo dispara `compile_pdf.sh`):

### Estrategia 1 — Typst (preferido)

1. Convertir el Markdown concatenado a Typst con Pandoc:

   ```
   pandoc {concat.md} -o {concat.typ} --to=typst
   ```

2. Concatenar `assets/manual-template.typ` (encabezado de plantilla) con el Typst convertido.
3. Compilar:

   ```
   typst compile {concat-con-template.typ} salida/manual.pdf
   ```

Ventajas: tiempos de compilación mucho menores, soporte nativo de Unicode y fuentes del sistema, errores claros.

### Estrategia 2 — XeLaTeX (fallback)

```
pandoc {concat.md} \
  -o salida/manual.pdf \
  --pdf-engine=xelatex \
  --toc --toc-depth=3 --number-sections \
  -V mainfont="DejaVu Sans" \
  -V monofont="DejaVu Sans Mono" \
  -V geometry:margin=2.5cm \
  -V lang={idioma} \
  -V documentclass=report
```

### Estrategia 3 — pdfLaTeX (último recurso)

Sólo si el contenido es estrictamente ASCII Latin-1. No recomendado para manuales en español por la limitación de fuentes y caracteres especiales.

```
pandoc {concat.md} \
  -o salida/manual.pdf \
  --pdf-engine=pdflatex \
  --toc --toc-depth=3 --number-sections \
  -V geometry:margin=2.5cm
```

## Tabla de contenido y numeración

| Recurso | DOCX | PDF (Typst) | PDF (LaTeX) |
|---------|------|-------------|-------------|
| TOC automática | `--toc` | `#outline()` en plantilla | `--toc` |
| Numeración | `--number-sections` | `#set heading(numbering: "1.")` | `--number-sections` |

Por convención:

| Tipo de sección | Numerar |
|-----------------|---------|
| `portada` | No (sin número de página visible) |
| `tabla-contenido-auto` | No |
| `introduccion`, `requisitos`, `acceso`, `modulo`, `tarea-paso-a-paso`, `troubleshooting` | Sí (1, 2, 3, ...) |
| `glosario`, `soporte` | Sí, al final del cuerpo principal |
| `apendice` | Sí, con letra (A, B, C, ...) |

`concatenate.py` inserta marcas para que Pandoc/Typst apliquen este esquema.

## Verificación post-compilación

Antes de declarar la fase 6 terminada, validar:

| Check | Criterio | Si falla |
|-------|----------|----------|
| DOCX existe | Archivo `salida/manual.docx` presente | Bloqueo |
| Tamaño DOCX | 0.1 MB ≤ tamaño ≤ 30 MB | Investigar |
| PDF existe (si pedido) | Archivo `salida/manual.pdf` presente | Bloqueo |
| Tamaño PDF | 0.5 MB ≤ tamaño ≤ 50 MB | Investigar |
| Páginas DOCX | dentro de ±20% de `paginas_objetivo` del brief | Advertencia |
| Capturas embebidas | conteo de imágenes referenciadas == archivos físicos en `capturas/` | Bloqueo |

## Salida

```
salida/
├── manual.docx
└── manual.pdf
```

Y un archivo `salida/compilacion.log` con stdout/stderr de Pandoc/Typst/LaTeX para diagnóstico.

## Anti-patrones

- Compilar sin haber concatenado en orden explícito (depender de glob).
- Usar `pdflatex` para contenido en español sin advertir limitaciones.
- Saltar la verificación post-compilación porque "los binarios se ven bien".
- Reescribir contenido durante la compilación: el compilador no edita prosa.
- Embeber capturas inexistentes: si una sección referencia un PNG ausente, abortar.

## Limpieza

Tras compilar correctamente, eliminar:

- El archivo concatenado intermedio (`/tmp/manual-{slug}-concat.md`).
- Conversiones intermedias Markdown→Typst.
- Logs de éxito (los de error se conservan en `salida/compilacion.log`).

No tocar `secciones/`, `capturas/`, `01-brief.md`, `02-plan.md`, `03-inventario.md`.
