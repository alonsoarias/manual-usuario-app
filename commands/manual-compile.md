---
description: Ejecuta sólo la fase 6 del workflow de manuales — compila las secciones a DOCX, HTML autocontenido y Markdown (vía Pandoc) y a PDF (Typst preferido, XeLaTeX/pdfLaTeX como fallback), según el formato que pida el brief. Soporta plantilla DOCX del cliente con membrete vía --reference-doc. Requiere secciones/ y capturas/ completos.
argument-hint: ""
---

# Fase 6 — Compilación DOCX/PDF/HTML/Markdown

Usa la skill `manual-compiler`. La skill verifica dependencias del entorno y aplica la estrategia de compilación apropiada.

## Formatos

Se compila cada formato que el brief (`01-brief.md`) marque en `formato`:

| Campo del brief | Script | Salida |
|-----------------|--------|--------|
| `formato.docx` | `compile_pandoc.sh --to docx` | `salida/manual.docx` |
| `formato.pdf` | `compile_pdf.sh` | `salida/manual.pdf` |
| `formato.html` | `compile_pandoc.sh --to html` | `salida/manual.html` (un solo archivo, imágenes embebidas) |
| `formato.markdown` | `compile_pandoc.sh --to gfm` | `salida/manual.md` + imágenes en `salida/web/` (rutas relativas) |

## Pre-requisitos

- `secciones/` con los `.md` del plan
- `secciones/00-INDICE.md` con orden explícito
- `capturas/MANIFIESTO.md`
- `01-brief.md`, `02-plan.md`, `03-inventario.md`

## Dependencias del entorno

| Dependencia | Para qué |
|-------------|----------|
| `pandoc` | DOCX, HTML, Markdown y conversión Markdown→Typst (obligatorio) |
| `python3` | Concatenador (obligatorio) |
| `typst` | PDF preferido |
| `xelatex` | PDF de fallback |
| `pdflatex` | PDF de último recurso |

Si falta Pandoc, abortar. Si faltan motores PDF, advertir y compilar sólo los formatos de Pandoc.

## Salida esperada

```
salida/
├── manual.docx        (formato.docx)
├── manual.pdf         (formato.pdf)
├── manual.html        (formato.html)
├── manual.md          (formato.markdown)
├── web/               (imágenes de manual.md)
└── compilacion.log    (stdout/stderr de los scripts, para diagnóstico)
```

## Verificaciones post-compilación

- Tamaño DOCX entre 0.1 MB y 30 MB
- Tamaño PDF entre 0.5 MB y 50 MB
- Capturas embebidas == capturas referenciadas
- Páginas: el compilador sólo avisa; la tolerancia (check C4) la fija y la aplica `/manual-verify` (skill `manual-verifier`)

## Plantilla del cliente

Si `01-brief.md` declara `formato.reference_doc_path`, el compilador la pasa a `--reference-doc` de Pandoc. La plantilla aporta membrete, estilos de párrafo, márgenes y encabezados/pies.
