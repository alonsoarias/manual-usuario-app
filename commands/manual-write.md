---
description: Ejecuta sólo la fase 5 del workflow de manuales — redacta cada sección con un subagente fresco siguiendo plantillas por tipo de sección y reglas de tono. Aplica 8 criterios de review bloqueantes antes de aceptar cada sección. Requiere 02-plan.md, 03-inventario.md y capturas/ presentes.
argument-hint: ""
---

# Fase 5 — Redacción por subagentes

Usa la skill `manual-writer` para producir las secciones del manual. Por defecto en serie; en modo `--rapido` puede paralelizar siempre que respete los criterios de review.

## Pre-requisitos

- `01-brief.md`, `02-plan.md`, `03-inventario.md` con `borrador: false`
- `capturas/MANIFIESTO.md` con todas las capturas en estado OK o pendientes manuales conocidas

## Salida esperada

- `secciones/{ID}-{slug}.md` por cada sección no-TOC del plan.
- `secciones/00-INDICE.md` con el orden explícito que el compilador usará.

Cada sección con frontmatter (`seccion_id`, `titulo`, `tipo`, `audiencia`, `paginas_estimadas`, `capturas`, `fuentes_inventario`).

## Criterios de review (bloqueantes)

| W1 | Cumple criterio de hecho del plan |
| W2 | Capturas referenciadas existen físicamente |
| W3 | Nombres de UI coinciden literal con el inventario |
| W4 | Sin marcadores [TODO]/[VERIFICAR]/lorem ipsum |
| W5 | Sigue plantilla del tipo de sección |
| W6 | Páginas reales dentro de ±50% de la estimación (advertencia si fuera) |
| W7 | Voz activa, presente, segunda persona en ≥90% de frases |
| W8 | Sin adjetivos vacíos (intuitivo, fácil, potente, amigable, etc.) |

Máx 3 iteraciones por sección antes de escalar al usuario.
