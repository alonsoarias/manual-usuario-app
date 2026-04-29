---
description: Ejecuta sólo la fase 2 del workflow de manuales — convierte 01-brief.md en un plan estructurado de secciones atómicas con criterios de hecho y capturas requeridas. Requiere 01-brief.md aprobado.
argument-hint: ""
---

# Fase 2 — Plan de secciones

Usa la skill `manual-planner` para producir el plan a partir del brief aprobado.

## Pre-requisitos

`01-brief.md` con `borrador: false`. Si no existe, abortar y devolver el control a `/manual-brainstorm`.

## Salida esperada

`02-plan.md` con:

- Frontmatter YAML (`borrador: false`, total de secciones, total de páginas estimadas, ambiente de capturas).
- Tabla resumen con todas las secciones (ID, título, tipo, audiencia, capturas, páginas, criterio de hecho).
- Detalle por sección con tareas que cubre, criterio de hecho objetivo, notas.

## Reglas que aplica la skill

- Cada sección es una tarea atómica autocontenida (2-5 minutos para un subagente fresco).
- Máx 5 páginas por sección — si pasa, dividir.
- IDs correlativos sin huecos (S00, S01, S02...).
- Criterios de hecho verificables por observación, no subjetivos.
- Sin solapes entre secciones.
- Calibración con la profundidad declarada.

Si el plan queda incompleto, la skill no lo marca como aprobado y bloquea las fases siguientes.
