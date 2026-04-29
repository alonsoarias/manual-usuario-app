---
description: Ejecuta sólo la fase 1 del workflow de manuales — brainstorming socrático en 3 bloques de preguntas que produce 01-brief.md. No requiere artefactos previos.
argument-hint: "[nombre-app]"
---

# Fase 1 — Brainstorming socrático

Aplicación a documentar: **$ARGUMENTS**

Usa la skill `manual-brainstormer` para conducir las 8 preguntas críticas en 3 bloques:

- **Bloque A — Identidad** (nombre comercial/técnico, versión, tipo de aplicación)
- **Bloque B — Audiencia** (perfil específico, tareas concretas)
- **Bloque C — Alcance y formato** (módulos in/out, formato DOCX/PDF, profundidad)

## Pre-requisitos

Ninguno. Esta es la primera fase del workflow.

## Salida esperada

`{cwd}/manual-{slug-app}-{YYYY-MM-DD}/01-brief.md` con:

- Frontmatter YAML completo (`borrador: false`).
- Identidad de la app, audiencia, tareas, alcance, formato, profundidad.
- Idioma del manual.

## Validaciones que aplica la skill

- Sin campos vacíos ni "TBD".
- Audiencia descrita en al menos 5 palabras concretas.
- Entre 5 y 15 tareas en infinitivo.
- Profundidad coherente con `paginas_objetivo`.

Si el brief queda incompleto, la skill no lo marca como aprobado y bloquea las fases siguientes.
