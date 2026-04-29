---
description: Ejecuta sólo la fase 6 del workflow de manuales — compila las secciones a DOCX (vía Pandoc) y PDF (Typst preferido, XeLaTeX/pdfLaTeX como fallback). Soporta plantilla DOCX del cliente con membrete vía --reference-doc. Requiere secciones/ y capturas/ completos.
argument-hint: ""
---

# Fase 6 — Compilación DOCX/PDF

Usa la skill `manual-compiler`. La skill verifica dependencias del entorno y aplica la estrategia de compilación apropiada.

## Pre-requisitos

- `secciones/` con los `.md` del plan
- `secciones/00-INDICE.md` con orden explícito
- `capturas/MANIFIESTO.md`
- `01-brief.md`, `02-plan.md`, `03-inventario.md`

## Dependencias del entorno

| Dependencia | Para qué |
|-------------|----------|
| `pandoc` | DOCX y conversión Markdown→Typst (obligatorio) |
| `python3` | Concatenador (obligatorio) |
| `typst` | PDF preferido |
| `xelatex` | PDF de fallback |
| `pdflatex` | PDF de último recurso |

Si falta Pandoc, abortar. Si faltan motores PDF, advertir y compilar sólo DOCX.

## Salida esperada

- `salida/manual.docx` (si el brief lo pidió)
- `salida/manual.pdf` (si el brief lo pidió)
- `salida/compilacion.log` con stdout/stderr para diagnóstico

## Verificaciones post-compilación

- Tamaño DOCX entre 0.1 MB y 30 MB
- Tamaño PDF entre 0.5 MB y 50 MB
- Capturas embebidas == capturas referenciadas
- Páginas dentro de ±20% de `paginas_objetivo` (advertencia si fuera)

## Plantilla del cliente

Si `01-brief.md` declara `formato.reference_doc_path`, el compilador la pasa a `--reference-doc` de Pandoc. La plantilla aporta membrete, estilos de párrafo, márgenes y encabezados/pies.
