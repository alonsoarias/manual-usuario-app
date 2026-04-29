---
name: manual-writer
description: Activar en la fase 5 del workflow de manuales o por el comando /manual-write. Redacta cada sección del manual usando subagentes frescos, uno por sección, con review entre etapas y persona de technical writer senior. Requiere 02-plan.md, 03-inventario.md y capturas/ (fase 4) completas. Produce los archivos secciones/{ID}-{slug}.md.
---

# Skill: manual-writer

Fase 5 del workflow. La única que produce prosa real. Usa el patrón **subagent-driven development**: cada sección la redacta un subagente fresco que recibe sólo lo que necesita, con criterios de review bloqueantes antes de aceptar el resultado.

## Pre-requisitos (regla 1)

Verificar que existen y están aprobados:

- `01-brief.md` con `borrador: false`
- `02-plan.md` con `borrador: false`
- `03-inventario.md` con `borrador: false`
- `capturas/MANIFIESTO.md` con todas las capturas marcadas OK o pendientes manuales conocidas

Si falta cualquiera, **abortar** y devolver a la fase pendiente.

## Principio rector — un subagente por sección

Cada sección de `02-plan.md` se redacta en un subagente fresco. El subagente recibe:

1. El bloque del brief con el perfil de audiencia y la profundidad.
2. Su sección específica del plan (con ID, tipo, capturas requeridas, criterio de hecho, páginas estimadas).
3. Las entradas del inventario que correspondan a las pantallas de su sección.
4. Las referencias a las capturas (no las imágenes binarias, sólo las rutas).
5. La plantilla del tipo de sección (`section-templates.md`).
6. Las reglas de tono y voz (`tone-and-voice.md`).

**El subagente no ve secciones de otros subagentes.** No ve el manual completo. Esa restricción evita que reproduzca contenido ya cubierto y mantiene foco.

Consultar `references/tone-and-voice.md` para reglas de redacción, `references/section-templates.md` para las plantillas por tipo.

## Persona del subagente

> Eres un **technical writer senior** con 10+ años de experiencia escribiendo manuales de usuario de software. Tu redacción es:
>
> - **Voz activa**, presente, segunda persona ("haga clic", "escriba", "verá").
> - **Frases cortas**: ≤15 palabras (TIC bajo), ≤25 (medio), ≤35 (alto).
> - **Un verbo por paso**: "haga clic en Guardar" — no "haga clic en Guardar y espere a que cargue".
> - **Describes lo que el usuario ve y hace**. No interpretas, no opinas, no editorializas.
> - **Usas el texto literal del inventario** para nombres de elementos de UI y mensajes del sistema. Si el inventario dice "Iniciar sesión", no escribes "iniciar la sesión" ni "logear" ni "ingresar al sistema".
> - **Evitas adjetivos vacíos**: nada de "intuitivo", "fácil de usar", "potente", "amigable", "moderno".

## Criterios de review (bloqueantes)

El subagente entrega un borrador. Antes de aceptarlo y guardarlo en `secciones/{ID}-{slug}.md`, el `manual-writer` verifica:

| # | Criterio | Si falla |
|---|----------|----------|
| W1 | Cumple el criterio de hecho declarado en el plan para esa sección | Re-encargar con feedback específico |
| W2 | Cada captura referenciada existe físicamente en `capturas/` | Bloqueo — falta captura, devolver a fase 4 |
| W3 | Nombres de elementos de UI coinciden literal con `03-inventario.md` | Re-encargar señalando las discrepancias |
| W4 | Sin marcadores `[TODO]`, `[VERIFICAR]`, `[XXX]`, `TBD`, `lorem ipsum` | Re-encargar |
| W5 | Sigue la plantilla del tipo de sección (encabezados, secciones obligatorias, orden) | Re-encargar |
| W6 | Páginas reales caen dentro de ±50% de la estimación del plan (si está muy fuera, advertir) | Advertencia, no bloqueo |
| W7 | Voz activa, presente, segunda persona en al menos 90% de las frases | Re-encargar |
| W8 | Sin adjetivos vacíos (lista en `tone-and-voice.md`) | Re-encargar |

Si un criterio falla, el subagente recibe el borrador devuelto + instrucción específica del criterio fallido. No más de 3 iteraciones por sección: tras la 3ª, escalar al usuario.

## Estructura de cada `secciones/{ID}-{slug}.md`

Frontmatter YAML obligatorio + contenido en Markdown:

```markdown
---
seccion_id: "S05"
titulo: "Acceso al sistema"
tipo: "acceso"
audiencia: "..."                       # heredada del brief o sub-perfil del plan
paginas_estimadas: 3
capturas:
  - "S05-pantalla-login.png"
  - "S05-pantalla-login-error.png"
fuentes_inventario:
  - "Login (Pantalla de inicio)"
  - "Mensajes de auth"
---

# Acceso al sistema

(contenido de la sección, redactado siguiendo plantilla y reglas)
```

El nombre del archivo es `{ID}-{slug}.md`, donde `slug` es el título de la sección en kebab-case ASCII.

## Workflow de la skill

1. Leer plan, inventario y manifiesto.
2. Para cada sección del plan en orden de ID:
   1. Si la sección es tipo `tabla-contenido-auto`, **saltar** (la genera el compilador).
   2. Si es tipo `portada` con plantilla, generar directamente con datos del brief (no requiere subagente).
   3. Para el resto, preparar el contexto del subagente:
      - Bloque relevante del brief (audiencia, profundidad, idioma).
      - Sección del plan.
      - Filas relevantes del inventario.
      - Plantilla del tipo de sección (texto literal copiado de `section-templates.md`).
      - Reglas de tono.
   4. Encargar al subagente la redacción.
   5. Aplicar criterios W1-W8.
   6. Si pasa, guardar en `secciones/{ID}-{slug}.md`.
   7. Si no, re-encargar (máx 3 veces).
3. Generar `secciones/00-INDICE.md` con la lista en orden.
4. Reportar al usuario:
   - secciones producidas
   - secciones bloqueadas (con criterio fallido)
   - capturas referenciadas pero ausentes (bloqueante)

## Entregables

- `secciones/S00-portada.md`, `secciones/S01-tabla-contenido-auto.md` (puede ser stub vacío con sólo frontmatter), ..., `secciones/S{N}-{slug}.md`
- `secciones/00-INDICE.md` (lista ordenada para que el compilador no dependa de glob ordering)

## Anti-patrones

- Redactar todas las secciones en un único agente "para ahorrar tiempo".
- Inventar funcionalidades no presentes en inventario.
- Cambiar nombres de elementos de UI "para que suenen mejor".
- Usar voz pasiva ("se hace clic en Guardar").
- Adjetivos vacíos: intuitivo, fácil, potente, amigable, moderno, robusto, eficiente.
- Frases largas con múltiples verbos por paso.
- Saltarse el review.
- Aceptar capturas que el plan exige pero que no existen físicamente.
- Saltarse secciones del plan "porque no aplican": si no aplican, deben removerse del plan, no ignorarse.

## Modo serial vs paralelo

Por defecto, redactar secciones en serie (1, 2, 3...). En modo `--rapido` se puede paralelizar lanzando subagentes simultáneos siempre que:

- No haya dependencias entre secciones.
- El review se ejecute por el `manual-writer` central, no por los subagentes.
- Se respete el límite de 3 iteraciones por sección.

El paralelismo no aplica a las secciones de tipo `portada`, `tabla-contenido-auto`, `glosario` (que dependen del resto del manual) ni a `apendice` que indexa otras secciones.
