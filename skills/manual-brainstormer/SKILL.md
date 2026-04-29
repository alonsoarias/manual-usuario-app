---
name: manual-brainstormer
description: Activar al inicio del flujo de manuales (fase 1), por el comando /manual-brainstorm, o cuando el usuario pida redactar un manual sin haber definido alcance, audiencia ni formato.
---

# Skill: manual-brainstormer

Fase 1 del workflow. Convierte una petición vaga ("hazme un manual de mi app") en un brief estructurado, ejecutable y aprobado por el usuario.

## Principio rector

No se redacta nada hasta saber qué se está documentando, para quién y con qué profundidad. El brainstorming es **socrático**: preguntas en bloques pequeños, una respuesta a la vez, sin avanzar al bloque siguiente hasta cerrar el actual.

Consultar `references/audience-profiles.md` para calibrar la profundidad y el tono según el perfil de audiencia identificado.

## Las 8 preguntas críticas (en 3 bloques)

### Bloque A — Identidad de la aplicación (3 preguntas)

A1. **Nombre comercial y nombre técnico** — ¿con qué nombre la conocen los usuarios finales? ¿hay un nombre interno/técnico distinto que aparece en el código o la URL?

A2. **Versión a documentar** — ¿qué versión específica? Si no hay versionado formal, ¿fecha de corte del estado actual?

A3. **Tipo de aplicación** — escoger una y sólo una de:
- Web (SaaS, intranet, portal)
- Móvil (iOS, Android, híbrida)
- Escritorio (Windows, macOS, Linux)
- Plataforma CMS (Moodle, WordPress, OJS, Drupal, Joomla, etc.)
- Híbrida (especificar combinación)

### Bloque B — Audiencia (2 preguntas)

B1. **Perfil específico del usuario final** — describir en una frase quién va a leer este manual. Nivel TIC esperado (bajo/medio/alto), edad típica, contexto de uso. **No aceptar respuestas como "todos los usuarios" o "el público general"**: insistir hasta tener un perfil concreto.

B2. **Tareas concretas** — listar entre 5 y 15 tareas que el usuario final ejecutará con la aplicación. Cada tarea debe ser un verbo en infinitivo + objeto directo (ej. "matricularse en un curso", "subir un comprobante de pago", "consultar el historial"). Si el usuario produce menos de 5, preguntar más; si pasa de 15, pedir priorización.

### Bloque C — Alcance y formato (3 preguntas)

C1. **Módulos incluidos y excluidos** — ¿qué partes de la app entran al manual? ¿qué partes explícitamente no? Si hay áreas administrativas que el usuario final no toca, excluirlas (regla YAGNI).

C2. **Formato de entrega** — DOCX, PDF o ambos. Si el cliente entrega plantilla DOCX con membrete, registrar la ruta para usarla en `--reference-doc` durante la compilación.

C3. **Profundidad** — escoger una de:
- **Quickstart** (5-15 páginas) — sólo el camino feliz de las tareas más comunes.
- **Estándar** (20-50 páginas) — todas las tareas listadas en B2, una sección por tarea o módulo.
- **Exhaustivo** (60+ páginas) — incluye configuración, troubleshooting, casos límite, glosario extendido y apéndices.

## Reglas de conducción del brainstorming

- Hacer **un bloque a la vez**. No mezclar preguntas de bloques distintos.
- Dentro de un bloque, hacer **todas** las preguntas; no aceptar respuestas parciales.
- Si la respuesta es ambigua, repreguntar hasta tener algo concreto. Ejemplo: si el usuario dice "todo el mundo lo usa", pedir un perfil específico antes de continuar.
- No sugerir respuestas: dejar que el usuario decida.
- Si el usuario no sabe la respuesta de A1/A2/A3, preguntar dónde puede consultarse.

## Anti-patrones (qué no hacer)

- Hacer las 8 preguntas de un golpe en un bloque único.
- Asumir el perfil de audiencia a partir del tipo de app.
- Asumir profundidad estándar sin preguntar.
- Pasar a la fase 2 con campos del brief vacíos o marcados como "TBD".
- Redactar prosa de relleno en el brief (descripciones largas de la app, contexto no solicitado).

## Salida obligatoria: `01-brief.md`

Estructura YAML-like al inicio del archivo, seguida de notas opcionales en Markdown:

```markdown
---
borrador: false
nombre_comercial: "..."
nombre_tecnico: "..."
slug: "..."                          # kebab-case ASCII derivado de nombre_comercial
version: "..."
fecha_corte: "YYYY-MM-DD"
tipo_aplicacion: "web | movil | escritorio | cms | hibrida"
tipo_detalle: "..."                  # ej. "Laravel 10 + Vue 3 SPA", "Moodle 4.3"

audiencia:
  perfil: "..."                      # 1 frase concreta
  nivel_tic: "bajo | medio | alto"
  contexto_uso: "..."                # ej. "lectoría desde móvil en horarios laborales"

tareas:
  - "..."                            # entre 5 y 15
  - "..."

alcance:
  modulos_incluidos:
    - "..."
  modulos_excluidos:
    - "..."

formato:
  docx: true | false
  pdf: true | false
  reference_doc_path: ""             # ruta absoluta o vacío

profundidad: "quickstart | estandar | exhaustivo"
paginas_objetivo: 30                 # rango: quickstart 5-15, estandar 20-50, exhaustivo 60+

idioma: "..."                        # ej. "es", "en"
---

## Notas adicionales del usuario

(Texto libre opcional. Si está vacío, omitir esta sección.)
```

## Validaciones antes de marcar borrador: false

Antes de cerrar la fase, verificar:

- `nombre_comercial`, `slug`, `version`, `tipo_aplicacion` no vacíos.
- `audiencia.perfil` tiene al menos 5 palabras y no es genérico ("todos", "público").
- `tareas` tiene entre 5 y 15 entradas, todas en infinitivo.
- `alcance.modulos_incluidos` no vacío.
- `formato.docx` o `formato.pdf` (al menos uno) en `true`.
- `profundidad` y `paginas_objetivo` coherentes (quickstart ≤15, estándar 20-50, exhaustivo ≥60).

Si alguna validación falla, mostrar al usuario el problema y pedir corregir antes de avanzar a la fase 2.
