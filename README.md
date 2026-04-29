# manual-usuario-app

Plugin de Claude Code para generar **manuales de usuario profesionales en DOCX y PDF** de cualquier aplicación de software (web, móvil, escritorio o plataformas CMS), con captura automática de pantallas vía MCPs de browser y un workflow socrático de 7 fases con verificación basada en evidencia. Genérico y reutilizable: sin acoplamientos a clientes, marcas o stacks concretos.

## Las 7 fases

| # | Fase | Skill responsable | Artefacto producido |
|---|------|-------------------|---------------------|
| 1 | Brainstorming socrático | `manual-brainstormer` | `01-brief.md` |
| 2 | Plan de secciones | `manual-planner` | `02-plan.md` |
| 3 | Análisis de la aplicación | `app-analyzer` | `03-inventario.md` |
| 4 | Captura de pantallas | `screenshot-capturer` | `capturas/*.png` + `MANIFIESTO.md` |
| 5 | Redacción por subagentes | `manual-writer` | `secciones/*.md` |
| 6 | Compilación DOCX/PDF | `manual-compiler` | `salida/manual.{docx,pdf}` |
| 7 | Verificación de calidad | `manual-verifier` | `verificacion.md` |

Coordinadas por la skill `manual-orchestrator`, con checkpoints humanos después de las fases 1, 2 y 3.

## Tres reglas innegociables

1. **No saltar fases.** Cada fase produce un artefacto que la siguiente verifica.
2. **Evidencia antes de afirmaciones.** La fase 7 siempre se ejecuta; su informe se muestra completo.
3. **YAGNI documental.** No se documenta lo que la app no tiene ni lo que el cliente no usa.

## Instalación

Clonar el repositorio y registrarlo como marketplace local:

```
/plugin marketplace add /ruta/al/manual-usuario-app
/plugin install manual-usuario-app@manual-usuario-app-marketplace
```

O, si prefieres referenciar por URL Git:

```
/plugin marketplace add https://github.com/{owner}/manual-usuario-app
/plugin install manual-usuario-app@manual-usuario-app-marketplace
```

## Comandos disponibles

| Comando | Efecto |
|---------|--------|
| `/manual [nombre-app]` | Workflow completo (7 fases) con checkpoints |
| `/manual [nombre-app] --rapido` | Workflow completo sin checkpoints intermedios; fase 7 sigue siendo obligatoria |
| `/manual-brainstorm` | Sólo fase 1 |
| `/manual-plan` | Sólo fase 2 |
| `/manual-analyze` | Sólo fase 3 |
| `/manual-capture` | Sólo fase 4 |
| `/manual-write` | Sólo fase 5 |
| `/manual-compile` | Sólo fase 6 |
| `/manual-verify` | Sólo fase 7 |

Cada comando aislado verifica los pre-requisitos antes de ejecutar (regla 1).

## Dependencias del entorno

| Dependencia | Para qué | Obligatorio |
|-------------|----------|-------------|
| `pandoc` (≥ 2.19) | DOCX, conversión Markdown→Typst | Sí |
| `python3` (≥ 3.8) | Concatenación, post-proceso | Sí |
| `Pillow` (Python) | Anotaciones y validación de imágenes | Recomendado |
| `typst` | PDF preferido | Recomendado |
| `xelatex` | PDF de fallback | Alternativo a Typst |
| `pdflatex` | PDF de último recurso | Sólo contenido ASCII |
| `pdftotext` (poppler) | Verificación de PDF en fase 7 | Recomendado |
| Fuentes DejaVu Sans / DejaVu Sans Mono | Plantilla por defecto | Recomendado |

Para captura automática de pantallas, al menos uno:

- **Playwright MCP** (preferido): `claude mcp add playwright npx '@playwright/mcp@latest'`
- **Chrome DevTools MCP** (cuando se necesita la sesión real del usuario)
- **Puppeteer MCP**

Si no hay ninguno, el plugin produce `capturas/INSTRUCCIONES.md` con pasos para captura manual.

## Estructura del directorio de trabajo

Por cada manual, el plugin crea una carpeta única en el directorio actual:

```
manual-{slug-app}-{YYYY-MM-DD}/
├── 01-brief.md
├── 02-plan.md
├── 03-inventario.md
├── capturas/
│   ├── MANIFIESTO.md
│   └── *.png
├── secciones/
│   ├── 00-INDICE.md
│   └── {ID}-{slug}.md
├── salida/
│   ├── manual.docx
│   └── manual.pdf
└── verificacion.md
```

## Inspiraciones

El diseño combina lo mejor de cinco proyectos de la comunidad Claude Code:

- [obra/superpowers](https://github.com/obra/superpowers) — workflow socrático en fases con artefactos verificables, brainstorming previo, planes en tareas atómicas, subagentes frescos por tarea, evidencia antes de afirmaciones.
- [glincker/readme-generator](https://github.com/glincker/readme-generator) — análisis automático de la app cruzando código y UI.
- [danielrosehill/user-manual-plugin](https://github.com/danielrosehill/user-manual-plugin) — compilación modular DOCX/PDF con Typst preferido y Pandoc fallback.
- [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) — persona "technical writer senior" en el redactor.
- [levnikolaevich/ln-100-documents-pipeline](https://github.com/levnikolaevich/ln-100-documents-pipeline) — pipeline modo File sin dependencias externas pesadas.

## Licencia

MIT — ver `LICENSE`.
