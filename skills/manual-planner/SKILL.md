---
name: manual-planner
description: Activar en la fase 2 del workflow de manuales o por el comando /manual-plan. Convierte el brief 01-brief.md en un plan estructurado de secciones donde cada sección es una tarea atómica autocontenida que un subagente fresco puede completar en 2-5 minutos. Requiere 01-brief.md presente y aprobado.
---

# Skill: manual-planner

Fase 2 del workflow. Transforma el brief en un plano de obra. Define una sección por unidad de trabajo, con criterio de hecho explícito, capturas requeridas listadas y tamaño estimado. Sin plan, no hay fase 3, 4 ni 5.

## Pre-requisito (regla 1)

Verificar que existe `01-brief.md` con `borrador: false`. Si no existe o está marcado borrador, **abortar** y devolver al usuario al comando `/manual-brainstorm`.

## Principio rector

Cada sección del plan es una **tarea atómica autocontenida**: un subagente fresco, sin contexto previo, debe poder completarla en 2-5 minutos teniendo a mano:

- el brief (01-brief.md)
- el inventario (03-inventario.md)
- las capturas relevantes a su ID de sección

Si una sección no cumple esa propiedad, dividirla.

Consultar `references/manual-structures.md` para plantillas por profundidad y por tipo de aplicación.

## Entradas

- `01-brief.md` (obligatorio)
- `references/manual-structures.md` (interno a la skill)

## Salida obligatoria: `02-plan.md`

Estructura YAML al inicio + tabla de secciones en Markdown:

```markdown
---
borrador: false
profundidad: "..."                   # heredada del brief
total_secciones: N
total_paginas_estimadas: N
ambiente_capturas:
  viewport_desktop: "1366x768"
  viewport_movil: "375x812"
  idioma_ui: "..."                   # debe coincidir con brief.idioma
---

# Plan de secciones

| ID | Título | Tipo | Audiencia | Capturas | Páginas | Criterio de hecho |
|----|--------|------|-----------|----------|---------|-------------------|
| S00 | Portada | portada | todos | 0 | 1 | Contiene título, versión, fecha, idioma |
| S01 | Tabla de contenido | tabla-contenido-auto | todos | 0 | 1-2 | Generada por compilador |
| ... | ... | ... | ... | ... | ... | ... |

## Detalle por sección

### S{NN} — {título}

- **Tipo:** {portada | tabla-contenido-auto | introduccion | requisitos | acceso | modulo | tarea-paso-a-paso | troubleshooting | glosario | soporte | apendice}
- **Audiencia:** {perfil heredado del brief o sub-perfil}
- **Páginas estimadas:** {número o rango}
- **Capturas requeridas:**
  - `{ID-seccion}-{descripcion}.png` — {qué pantalla, en qué estado}
- **Tareas que cubre:** (sólo si tipo = tarea-paso-a-paso o modulo)
  - {verbo + objeto, copiado literal del brief}
- **Criterio de hecho:**
  - {bullet list de condiciones objetivas y verificables}
- **Notas:**
  - {opcional, supuestos o dependencias}

### S{NN+1} — ...
```

## Reglas de construcción del plan

### R1 — Una sección no excede 5 páginas

Si la estimación supera 5 páginas, dividir en sub-secciones (ej. una sección "Configuración" de 8 páginas se vuelve "Configuración general" + "Configuración avanzada"). Cada sub-sección obtiene su propio ID.

### R2 — IDs estrictamente correlativos

`S00`, `S01`, `S02`, ... sin saltos. Si después de aprobado el plan se inserta una sección, renumerar todo y advertir al usuario.

### R3 — Sin secciones huérfanas

Cada sección del plan debe corresponder a:
- una tarea del bloque B2 del brief, o
- un módulo del alcance, o
- una sección de soporte estándar (portada, TOC, intro, acceso, glosario, soporte, apéndices, troubleshooting).

**No inventar secciones que el brief no autorice.** Si el redactor cree que falta algo, pedir al usuario actualizar el brief, no añadirlo silenciosamente.

### R4 — Capturas listadas con nombre exacto

El nombre de archivo PNG debe seguir el formato `{ID}-{descripcion-kebab}.png`. Por ejemplo: `S03-pantalla-login-error.png`. Esto permite que la fase 4 produzca los archivos sin ambigüedad y que la fase 5 los referencie sin escribir rutas a mano.

### R5 — Criterio de hecho objetivo

El criterio de hecho de cada sección debe ser **verificable mediante observación**. Ejemplos válidos:

- "Incluye captura `S03-pantalla-login.png`."
- "Cada paso comienza con verbo en imperativo."
- "Contiene mensaje de error literal del inventario para credenciales inválidas."

Ejemplos no válidos:
- "Es claro y conciso."
- "Resulta útil para el usuario."
- "Cubre todos los casos."

### R6 — Sin solapes

Si dos secciones cubren la misma tarea o el mismo módulo, fusionar o dividir por sub-tarea. Detectar solapes comparando los campos "Tareas que cubre".

### R7 — Calibración con la profundidad

Total de secciones por profundidad (incluye portada, TOC, soporte y glosario):

| Profundidad | Total de secciones | Páginas totales |
|-------------|--------------------|-----------------|
| Quickstart | 6-12 | 5-15 |
| Estándar | 12-25 | 20-50 |
| Exhaustivo | 25-50 | 60+ |

Si el plan cae fuera del rango, ajustar dividiendo o fusionando.

## Tipos de sección

Los siguientes tipos son los únicos permitidos. La fase 5 tiene plantilla específica para cada uno (ver `manual-writer/references/section-templates.md`):

| Tipo | Uso |
|------|-----|
| `portada` | Página inicial con título, versión, fecha, idioma, logo cliente si lo hay |
| `tabla-contenido-auto` | Generada por Pandoc/Typst; el redactor no escribe contenido |
| `introduccion` | Qué es la app, alcance, audiencia, convenciones tipográficas |
| `requisitos` | Hardware/software/permisos previos al uso |
| `acceso` | Login, recuperación de contraseña, cierre de sesión |
| `modulo` | Visión panorámica de un módulo y su relación con otros |
| `tarea-paso-a-paso` | Una tarea concreta del brief, paso a paso |
| `troubleshooting` | Problemas comunes con su solución |
| `glosario` | Definiciones de términos específicos de la app |
| `soporte` | Cómo obtener ayuda, canales oficiales |
| `apendice` | Material complementario (atajos, convenciones, formatos) |

## Validaciones antes de marcar borrador: false

Antes de cerrar la fase 2, verificar:

- Existe al menos una sección `portada` y una `tabla-contenido-auto`.
- Cada tarea del bloque B2 del brief aparece en al menos una sección de tipo `tarea-paso-a-paso` o `modulo`.
- Total de secciones y páginas dentro del rango de la profundidad declarada.
- Todos los IDs son únicos y correlativos sin huecos.
- Cada sección tiene al menos un bullet en "Criterio de hecho".
- Suma de capturas estimadas es coherente con las tablas de calibración por nivel TIC.

Si alguna validación falla, mostrar al usuario el problema y pedir corregir antes de avanzar a la fase 3.

## Anti-patrones

- Crear secciones genéricas como "Funcionalidades adicionales" sin detalle.
- Omitir el campo "Capturas requeridas" porque "se decidirá luego".
- Producir un plan de 60 secciones para una app simple (sobreplaneación).
- Fusionar tareas distintas del brief en una sola sección "para ahorrar espacio".
- Inventar tareas no presentes en el brief.
