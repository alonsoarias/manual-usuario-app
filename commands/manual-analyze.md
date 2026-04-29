---
description: Ejecuta sólo la fase 3 del workflow de manuales — analiza la aplicación y produce 03-inventario.md con texto literal de la UI, formularios, mensajes, roles y discrepancias. Detecta automáticamente el nivel de acceso disponible. Requiere 02-plan.md aprobado.
argument-hint: "[ruta-codigo-fuente | url-app]"
---

# Fase 3 — Análisis de la aplicación

Recurso a inspeccionar: **$ARGUMENTS**

Usa la skill `app-analyzer`. La skill detecta el nivel de acceso disponible y aplica la estrategia apropiada:

- **Nivel 0** — sin acceso: pide descripciones y capturas previas al cliente.
- **Nivel 1** — código fuente accesible: usa `Glob`, `Grep`, `Read` y consulta `references/{web-app,mobile-app,desktop-app,cms-platform}.md` según el stack detectado.
- **Nivel 2** — app desplegada accesible: delega al `screenshot-capturer` para inspección dirigida.
- **Nivel 3** — combinado (recomendado): cruza código y UI desplegada y reporta discrepancias.

## Pre-requisitos

`02-plan.md` con `borrador: false`. Si no existe, abortar y devolver al usuario a `/manual-plan`.

## Salida esperada

`03-inventario.md` con tablas de:

1. Módulos y rutas
2. Formularios y campos (etiquetas literales)
3. Mensajes del sistema (texto literal)
4. Roles y permisos
5. Términos para glosario
6. Discrepancias detectadas

Cada fila con su columna **Evidencia** (ruta+línea, captura de inspección, o declaración del cliente).

## Reglas que aplica la skill

- **Texto literal**, sin paráfrasis.
- Sólo se inspecciona lo que el plan pide; lo demás va a "Discrepancias".
- Errores ortográficos en la UI se registran tal cual y se reportan, no se corrigen.
- Si el nivel es 0, advertir explícitamente que la verificación contra UI real no fue posible.
