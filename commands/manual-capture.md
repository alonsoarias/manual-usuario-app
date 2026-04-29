---
description: Ejecuta sólo la fase 4 del workflow de manuales — captura las pantallas listadas en el plan usando los MCPs de browser disponibles (Playwright, Chrome DevTools, Puppeteer) o produce instrucciones de captura manual como fallback. Requiere 02-plan.md y 03-inventario.md aprobados.
argument-hint: ""
---

# Fase 4 — Captura de pantallas

Usa la skill `screenshot-capturer`. La skill detecta automáticamente la herramienta disponible en el entorno y la usa en este orden de preferencia:

1. **Playwright MCP** (preferido) — ver `references/playwright-mcp.md`
2. **Chrome DevTools MCP** — útil cuando se necesita la sesión real del usuario; ver `references/chrome-devtools-mcp.md`
3. **Puppeteer MCP**
4. **CLI bash** (`npx playwright screenshot`, `chromium --headless`, `wkhtmltoimage`)
5. **Fallback manual** — produce `capturas/INSTRUCCIONES.md`; ver `references/manual-capture-fallback.md`

## Pre-requisitos

- `02-plan.md` con `borrador: false`
- `03-inventario.md` con `borrador: false`

Si falta cualquiera, abortar y devolver al usuario a la fase pendiente.

## Salida esperada

- `capturas/{ID-seccion}-{descripcion-kebab}.png` para cada captura listada en el plan.
- `capturas/MANIFIESTO.md` con el listado verificado (archivo, sección, tamaño, herramienta, estado).
- `capturas/INSTRUCCIONES.md` (sólo si hay capturas pendientes manuales).

## Reglas que aplica la skill

- Nombres de archivo idénticos a los declarados en el plan.
- Viewport heredado del plan (1366x768 desktop, 375x812 móvil por defecto).
- Sin información personal real en las capturas.
- Idioma de la UI = idioma declarado en el brief.
- Anotaciones (flechas, números) por inyección de overlays con `browser_evaluate` o post-proceso con Pillow.
