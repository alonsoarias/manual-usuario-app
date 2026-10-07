---
description: Ejecuta sólo la fase 7 del workflow de manuales — verificación de calidad obligatoria con 11 checks (C1-C11). Produce verificacion.md y un veredicto APROBADO o BLOQUEADO (invocado directamente es siempre una pasada completa, `alcance: completa`). Esta fase se ejecuta SIEMPRE, incluso en modo rápido. Sin este informe, el manual no se considera entregable.
argument-hint: ""
---

# Fase 7 — Verificación de calidad

Usa la skill `manual-verifier`. Ejecuta los 11 checks listados abajo y produce el informe en `verificacion.md`. El informe completo se muestra al usuario, no sólo el veredicto.

## Los 11 checks

| # | Check | Bloqueante |
|---|-------|------------|
| C1 | Conteo de secciones (plan vs secciones/ vs DOCX) | Sí |
| C2 | Capturas embebidas (manifiesto vs referenciadas vs físicas en DOCX) | Sí |
| C3 | Tamaño DOCX (0.1-30 MB) y PDF (0.5-50 MB) | Sí |
| C4 | Páginas vs estimación del plan (±40%) | No |
| C5 | Coincidencia UI con inventario (10 elementos muestreados) | No |
| C6 | Marcadores [VERIFICAR]/[TODO]/[XXX]/TBD/lorem ipsum | Sí |
| C7 | Tono y voz (5 párrafos muestreados) | No |
| C8 | DOCX abre sin error | Sí |
| C9 | PDF tiene texto seleccionable (>100 palabras vía pdftotext) | Sí |
| C10 | TOC presente con al menos 1 entrada por sección | Sí |
| C11 | Capturas de pasos accionables anotadas | Sí |

## Pre-requisitos

- `salida/manual.docx` (si el brief lo pidió)
- `salida/manual.pdf` (si el brief lo pidió)
- `secciones/`, `capturas/`, `01-brief.md`, `02-plan.md`, `03-inventario.md`

## Salida esperada

`verificacion.md` con:

- Frontmatter (fecha, veredicto, `ronda`, `alcance`, totales por estado). Este comando es siempre una pasada completa (`alcance: completa`), por lo que solo emite `APROBADO` o `BLOQUEADO`. El tercer veredicto, `PENDIENTE-PASADA-COMPLETA`, solo lo emite una re-verificación acotada dentro del bucle de corrección del orquestador y nunca es final.
- Tabla resumen con los 11 checks y su estado.
- Detalle por check con datos concretos y, si fallan, acción recomendada.
- Lista de advertencias no bloqueantes.
- Recomendación final: si APROBADO, listar la entrega; si BLOQUEADO, indicar qué fase re-ejecutar.

## Reglas

- **Bloqueo significa bloqueo.** Cualquier check bloqueante fallido produce veredicto `BLOQUEADO`.
- **Sin tocar el manual.** El verificador sólo lee y reporta.
- **Reproducible.** Salvo C5/C7 que muestrean al azar, otra ejecución sobre los mismos artefactos produce el mismo informe.
