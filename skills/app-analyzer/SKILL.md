---
name: app-analyzer
description: Activar en la fase 3 del workflow de manuales o por el comando /manual-analyze, cuando se necesita inventariar pantallas, rutas, formularios, mensajes del sistema y roles de cualquier aplicación (web, móvil, escritorio o CMS). Requiere 02-plan.md presente.
---

# Skill: app-analyzer

Fase 3 del workflow. Recolecta los datos crudos que necesitan las fases siguientes: rutas, formularios con etiquetas literales, mensajes del sistema, roles, permisos, términos para glosario y discrepancias detectadas. Sin inventario fiable, las capturas y la redacción se inventan.

## Pre-requisito (regla 1)

Verificar que existe `02-plan.md` con `borrador: false`. Si no existe, **abortar** y devolver al usuario al comando `/manual-plan`.

## Principio rector

**Texto literal**, no parafraseado. La regla más importante de esta fase: copiar palabra por palabra lo que aparece en la UI o en los mensajes del sistema. Si el botón dice "Guardar y continuar", el inventario dice "Guardar y continuar", no "Guardar".

Si la UI tiene errores tipográficos, el inventario los registra tal cual y los marca en la columna "Discrepancias".

## Los 4 niveles de inspección

El analyzer detecta el nivel de acceso y aplica la estrategia apropiada. Si el acceso disponible permite varios niveles, usar el combinado.

### Nivel 0 — Sin acceso a la aplicación

No hay código, no hay app desplegada, no hay credenciales. Sólo descripciones del cliente.

Estrategia:
- Pedir al cliente capturas previas, manuales antiguos, mockups o videos.
- Para cada sección del plan, pedir descripciones explícitas: "¿Qué dice exactamente el botón principal de la pantalla X? ¿Qué mensaje aparece tras un envío exitoso?"
- Marcar todo el inventario como `fuente: declarado-cliente` y advertir en la fase 7 que la verificación contra UI real no fue posible.

### Nivel 1 — Acceso al código fuente

Hay clonado el repositorio del cliente o un sub-conjunto inspeccionable.

Estrategia:
- Usar `Glob`, `Grep` y `Read` para descubrir rutas, vistas, modelos y mensajes.
- Consultar la guía específica del framework en `references/{web-app,mobile-app,desktop-app,cms-platform}.md`.
- Para cada hallazgo, registrar la ruta del archivo + número de línea como evidencia.
- Cuando la UI usa traducciones (i18n), buscar archivos `.po`, `.json`, `.yaml`, `.xml` con strings y registrar los textos del idioma declarado en el brief.

### Nivel 2 — Aplicación desplegada accesible

Hay URL/binario funcional pero no necesariamente código.

Estrategia:
- Delegar a la skill `screenshot-capturer` para capturas de inspección dirigida (no son las capturas finales del manual; son recolección de evidencia textual).
- Para cada vista del plan, navegar y leer literalmente la UI.
- Si la UI cambia con el rol del usuario, hacer una pasada por cada rol declarado en el brief.

### Nivel 3 — Combinado (código + app desplegada)

Mejor escenario. Cruza-verificar:
- Lo que dice el código vs lo que muestra la UI desplegada.
- Las traducciones del repo vs el idioma renderizado.
- Reportar cualquier divergencia en la columna "Discrepancias" del inventario.

## Salida obligatoria: `03-inventario.md`

Estructura YAML + tablas:

```markdown
---
borrador: false
nivel_inspeccion: "0 | 1 | 2 | 3"
fuente_principal: "codigo | app-desplegada | declarado-cliente | combinado"
ambiente_inspeccion:
  url: "..."                         # vacío si no aplica
  rol_inspeccionado: "..."           # rol con que se inspeccionó
  fecha: "YYYY-MM-DD"
discrepancias_detectadas: N
---

# Inventario de la aplicación

## 1. Módulos y rutas

| Módulo | Ruta / Pantalla | Tipo de acceso | Roles que acceden | Evidencia |
|--------|-----------------|----------------|-------------------|-----------|
| ... | `/dashboard` | autenticado | usuario, admin | `routes/web.php:42` |

## 2. Formularios y campos

| Pantalla | Campo (label literal) | Tipo | Obligatorio | Validaciones declaradas | Evidencia |
|----------|----------------------|------|-------------|-------------------------|-----------|
| Login | "Correo electrónico" | email | sí | RFC 5322 | `LoginForm.vue:18` |

## 3. Mensajes del sistema

| Contexto | Disparador | Texto literal | Idioma | Evidencia |
|----------|-----------|---------------|--------|-----------|
| Login fallido | credenciales inválidas | "Las credenciales no coinciden con nuestros registros." | es | `lang/es/auth.php:8` |

## 4. Roles y permisos

| Rol | Pantallas accesibles | Acciones permitidas | Acciones denegadas |
|-----|---------------------|---------------------|--------------------|
| ... | ... | ... | ... |

## 5. Términos para glosario

| Término | Definición operativa | Sinónimos en UI | Evidencia |
|---------|---------------------|-----------------|-----------|
| ... | ... | ... | ... |

## 6. Discrepancias detectadas

| # | Descripción | Severidad | Recomendación |
|---|-------------|-----------|---------------|
| 1 | El botón dice "Guardad" en lugar de "Guardar" | tipográfica | Reportar al cliente |
| 2 | Mensaje del sistema en inglés en una UI declarada como español | i18n | Reportar al cliente |
```

## Reglas de inspección

### R1 — Sólo lo que el plan pide

Inspeccionar únicamente las secciones, módulos y tareas listados en `02-plan.md`. No "explorar la app por curiosidad". Si durante la inspección aparece una funcionalidad relevante no listada en el plan, anotarla en "Discrepancias" pero **no** documentarla aún: requiere actualizar el brief y el plan.

### R2 — Sin paráfrasis

El texto del inventario es el texto que aparece en la UI o en el código. Si el redactor de la fase 5 quiere darle otra forma, lo hará en su sección, pero el inventario es la fuente de verdad literal.

### R3 — Evidencia obligatoria

Cada fila de las tablas debe tener una entrada en "Evidencia" con uno de:

- ruta de archivo + línea (nivel 1, 3): `app/Http/Controllers/AuthController.php:84`
- captura de inspección (nivel 2, 3): `inspeccion/0001-login.png`
- declaración del cliente (nivel 0): `declarado-cliente:correo-2025-XX-XX`

Sin evidencia, no se registra.

### R4 — Reportar discrepancias, no corregirlas

El analyzer **no** modifica la app del cliente. Si encuentra un error tipográfico, una traducción faltante o un mensaje inconsistente, lo registra en la sección 6 y deja la decisión al cliente. El redactor de la fase 5 usa el texto literal tal cual.

### R5 — Idioma declarado

El brief declara `idioma`. Si en la inspección aparecen strings en otros idiomas (mensajes del sistema en inglés mientras el manual será en español), reportar como discrepancia y, salvo indicación contraria, transcribir lo que aparece en pantalla.

## Validaciones antes de marcar borrador: false

- Toda sección del plan tiene al menos una entrada en "Módulos y rutas" o en "Formularios y campos" (excepto secciones de tipo `portada`, `tabla-contenido-auto`, `glosario`, `soporte`, `apendice`).
- Cada tabla tiene la columna "Evidencia" rellena en todas las filas.
- "Discrepancias detectadas" coincide con el contador del frontmatter.
- Si `nivel_inspeccion = 0`, advertencia explícita en el frontmatter (`fuente_principal: declarado-cliente`).

## Anti-patrones

- Parafrasear textos de la UI "para que suenen mejor".
- Inventar mensajes del sistema que no se pueden citar literalmente.
- Documentar funcionalidades fuera del alcance del plan.
- Saltarse la columna "Evidencia" porque "se ve obvio".
- Corregir errores ortográficos del cliente sin reportarlos.
- Inspeccionar con un rol distinto al declarado y mezclar pantallas.
