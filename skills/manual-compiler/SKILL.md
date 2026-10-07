---
name: manual-compiler
description: Activar en la fase 6 del workflow de manuales o por el comando /manual-compile, cuando se necesita compilar secciones Markdown a DOCX o PDF. Requiere secciones/ y capturas/ presentes.
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
pandoc --from=markdown-raw_tex-raw_attribute-tex_math_dollars {concat.md} \
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

Estrategia en cascada (lo dispara `compile_pdf.sh`). Si Typst está instalado y falla, el script termina con rc 5 y **no** cae a LaTeX (ver «Seguridad y códigos de salida»); LaTeX sólo se usa cuando Typst no está instalado:

### Estrategia 1 — Typst (preferido)

1. Convertir el Markdown concatenado a Typst con Pandoc:

   ```
   pandoc --from=markdown-raw_tex-raw_attribute-tex_math_dollars {concat.md} -o {concat.typ} --to=typst
   ```

2. Concatenar `assets/manual-template.typ` (encabezado de plantilla) con el Typst convertido.
3. Compilar:

   ```
   typst compile --root {ancestro-común-de-secciones-y-capturas} {concat-con-template.typ} salida/manual.pdf
   ```

Ventajas: tiempos de compilación mucho menores, soporte nativo de Unicode y fuentes del sistema, errores claros.

### Estrategia 2 — XeLaTeX (fallback)

```
pandoc --from=markdown-raw_tex-raw_attribute-tex_math_dollars {concat.md} \
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
pandoc --from=markdown-raw_tex-raw_attribute-tex_math_dollars {concat.md} \
  -o salida/manual.pdf \
  --pdf-engine=pdflatex \
  --toc --toc-depth=3 --number-sections \
  -V geometry:margin=2.5cm
```

## Seguridad y códigos de salida

El Markdown de `secciones/` lo redactan agentes a partir de la app analizada: **no es de confianza**. Por eso los cuatro comandos pandoc de arriba (DOCX, Typst, XeLaTeX, pdfLaTeX) llevan el MISMO `--from` —apaga TeX/OpenXML/Typst crudo y las matemáticas `$..$`—, que vive en una única fuente, `skills/manual-compiler/scripts/pandoc-from.txt`, leída por los scripts shell y por `concatenate.py`: la validación de imágenes parsea el Markdown exactamente como lo hará el motor (si difirieran, una imagen podría quedar oculta para la validación y visible para el motor). Un test exige esa igualdad.

| rc | Script | Significado |
|----|--------|-------------|
| 2 | `concatenate.py`, ambos `compile_*.sh` | Argumentos faltantes; o una imagen sale del manual, usa un esquema no permitido (`file:`, `ftp:`...), lleva `..` codificado (`%2e%2e`), NUL, consulta/fragmento (`?`/`#`), doble codificación, o es una referencia `![a][r]` con definición relativa. Sin salida escrita |
| 3 | `compile_*.sh` | Falta `pandoc`, `python3` o `concatenate.py` |
| 4 | `compile_pdf.sh` | Ningún motor PDF disponible o todos fallaron |
| 5 | `compile_pdf.sh` | **Typst está instalado y falló**: no hay fallback a LaTeX (un fallo de Typst provocable desde el contenido no debe degradar a un motor que ejecute TeX) o no se generó el PDF |
| 6 | `compile_pdf.sh` | `secciones/` o `capturas/` contienen enlaces simbólicos |
| 7 | `compile_docx.sh` | Los medios que añade el contenido a `word/media` incluyen archivos que no son imágenes (ver «qué cuenta como imagen»); se borra el DOCX |

Reglas que se derivan:

- Toda imagen local debe resolverse (realpath) **dentro del ancestro común de `secciones/` y `capturas/`**. Se validan sobre el AST de pandoc, así que cubre imágenes en línea, por referencia, en tablas y en metadatos. Las rutas relativas se reescriben a absolutas sólo para imágenes en línea `![alt](ruta)`; escribe los espacios como `%20`. Las definiciones por referencia (`[r]: ruta`) deben ser absolutas y canónicas (sin `..` ni enlaces).
- `concatenate.py` necesita `pandoc` para validar; sin él falla (rc 2) en vez de omitir la validación.
- Los enlaces simbólicos en secciones se omiten con aviso (`concatenate.py`) y el PDF los rechaza (rc 6).
- **Limitación conocida:** `realpath` no detecta enlaces duros (hardlinks): un hardlink a un archivo ajeno colocado dentro del manual pasa la validación.
- **Las matemáticas `$..$` salen como texto literal en TODOS los formatos** (DOCX, Typst, LaTeX): con `tex_math_dollars` activa una imagen puede quedar oculta dentro de un nodo Math para la validación y visible para el motor, y en LaTeX `\input` se ejecutaría. `$5`, `$10`, `$HOME` en código y tablas se ven tal cual.
- **Qué cuenta como imagen (rc 7):** extensiones `png, jpg, jpeg, gif, svg, webp` (web/capturas), `bmp, tif, tiff, ico` (ráster) y `emf, wmf, eps, pdf` (vectoriales y de documento). Los medios que ya trae la plantilla del cliente (`--reference-doc`, archivo de confianza; p. ej. un logo `.emf`) se ignoran en la comprobación, con cualquier extensión: sólo cuentan los añadidos por el contenido.
- `![alt](<ruta con espacios>)` (ruta entre ángulos) se rechaza: codifica los espacios como `%20`.
- Rutas con `%`, `?` o `#` en su nombre no se admiten en imágenes.

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
