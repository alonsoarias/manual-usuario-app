# manual-usuario-app

Plugin de [Claude Code](https://claude.com/claude-code) que genera **manuales de usuario profesionales** de cualquier aplicación de software (web, móvil, escritorio o CMS). Toma la app real, captura sus pantallas y entrega el manual en **DOCX, PDF, HTML y/o Markdown**, en **español, inglés o portugués**.

- **Socrático:** pregunta antes de escribir; no inventa funcionalidades.
- **Con evidencia:** una fase de verificación obligatoria (13 checks) decide si el manual es entregable.
- **Seguro con datos personales:** enmascara los datos en la pantalla *antes* de capturar.
- **Genérico:** sin clientes, marcas ni stacks concretos.

Versión actual: **2.0.0** (ver [CHANGELOG.md](CHANGELOG.md)).

## Inicio rápido

```
/plugin marketplace add alonsoarias/manual-usuario-app
/plugin install manual-usuario-app@manual-usuario-app-marketplace
```

Luego, en la carpeta donde quieras el manual:

```
/manual Mi App
/manual Mi App --idioma en
/manual Mi App --rapido
```

También puedes pedirlo en lenguaje natural («hazme un manual de usuario de mi aplicación»): la skill `manual-orchestrator` se activa sola.

Instalación desde un clon local:

```
/plugin marketplace add /ruta/al/manual-usuario-app
/plugin install manual-usuario-app@manual-usuario-app-marketplace
```

## Cómo funciona: 7 fases

| # | Fase | Skill | Artefacto | Checkpoint humano |
|---|------|-------|-----------|:-:|
| 1 | Brainstorming socrático | `manual-brainstormer` | `01-brief.md` | Sí |
| 2 | Plan de secciones | `manual-planner` | `02-plan.md` | Sí |
| 3 | Análisis de la aplicación | `app-analyzer` | `03-inventario.md` | Sí |
| 4 | Captura de pantallas | `screenshot-capturer` | `capturas/*.png` + `MANIFIESTO.md` | No |
| 5 | Redacción por subagentes | `manual-writer` | `secciones/*.md` | No |
| 6 | Compilación | `manual-compiler` | `salida/manual.{docx,pdf,html,md}` | No |
| 7 | Verificación de calidad | `manual-verifier` | `verificacion.md` | No (se muestra siempre) |

`manual-orchestrator` coordina las siete. Con `--rapido` se omiten los checkpoints 1-3 y se aplican valores por defecto (DOCX + PDF, viewport 1366x768); la fase 7 nunca se omite. Sin Typst ni LaTeX solo se compila el DOCX, con aviso.

### Tres reglas innegociables

1. **No saltar fases.** Cada fase consume el artefacto de la anterior; si falta, se aborta.
2. **Evidencia antes de afirmaciones.** Nada se declara terminado sin el informe de la fase 7.
3. **YAGNI documental.** No se documenta lo que la app no tiene ni lo que la audiencia no usa.

### Bucle de corrección

Si la verificación bloquea el manual, el orquestador corrige y re-verifica por **rondas** (máximo 5). Cada ronda re-verifica solo lo que cambió; únicamente una pasada **completa** puede emitir `APROBADO`. El progreso queda en `estado.md`, así que una sesión interrumpida se retoma donde quedó.

## Comandos

| Comando | Efecto |
|---------|--------|
| `/manual [app]` | Workflow completo con checkpoints |
| `/manual [app] --rapido` | Sin checkpoints intermedios |
| `/manual [app] --idioma es\|en\|pt` | Fija el idioma (por defecto `es`) |
| `/manual-brainstorm` | Solo fase 1 |
| `/manual-plan` | Solo fase 2 |
| `/manual-analyze` | Solo fase 3 |
| `/manual-capture` | Solo fase 4 |
| `/manual-write` | Solo fase 5 |
| `/manual-compile` | Solo fase 6 |
| `/manual-verify` | Solo fase 7 (siempre pasada completa) |

Cada comando suelto comprueba sus prerrequisitos antes de ejecutar.

## Formatos e idiomas

| Formato | Salida | Notas |
|---------|--------|-------|
| DOCX | `salida/manual.docx` | Admite plantilla del cliente con `formato.reference_doc_path` en el brief |
| PDF | `salida/manual.pdf` | Typst si está instalado; si no, XeLaTeX o pdfLaTeX |
| HTML | `salida/manual.html` | Autocontenido |
| Markdown | `salida/manual.md` + `salida/web/` | Con las imágenes |

El brief elige uno o varios. Cada idioma genera su propia carpeta (`manual-{slug}-{lang}-{fecha}/`, sin sufijo para `es`) con guía de redacción propia por idioma.

## Datos personales

Si el inventario marca una pantalla con `pii: sí`, el capturador sustituye los datos **en la propia pantalla antes de capturar**; nunca tacha el PNG después. Esa marca manda sobre `enmascarar: no` del plan; solo una `excepción: <motivo>` aprobada por el responsable lo evita. El check C13 bloquea el manual si queda alguna pantalla sin enmascarar. Procedimiento en `skills/screenshot-capturer/references/pii-masking.md`.

## Verificación: los 13 checks

| Check | Qué comprueba | Bloquea |
|-------|---------------|:-:|
| C1 | Conteo de secciones | Sí |
| C2 | Capturas embebidas | Sí |
| C3 | Tamaño de DOCX y PDF | Sí |
| C4 | Páginas frente a la estimación | Aviso |
| C5 | Textos de UI iguales al inventario | Aviso |
| C6 | Marcadores y placeholders sin resolver | Sí |
| C7 | Tono y voz | Aviso |
| C8 | El DOCX abre sin error | Sí |
| C9 | El PDF tiene texto seleccionable | Sí |
| C10 | Tabla de contenido presente | Sí |
| C11 | Capturas de pasos accionables anotadas | Sí |
| C12 | HTML/Markdown sin rutas locales ni contenido activo | Sí (si el brief los pide) |
| C13 | Datos personales enmascarados | Sí |

## Dependencias

| Dependencia | Para qué | Necesaria |
|-------------|----------|-----------|
| `pandoc` (probado con 3.7) | DOCX, HTML, Markdown y conversión a Typst | Sí |
| `python3` ≥ 3.8 | Concatenación, validación y verificadores | Sí |
| `Pillow` | Anotaciones y validación de imágenes | Recomendada |
| `typst` | PDF preferido | Recomendada |
| `xelatex` / `pdflatex` | PDF alternativo (pdflatex solo ASCII) | Alternativa a Typst |
| `pdftotext` (poppler) | Verificar el PDF en la fase 7 (C9, C13) | Necesaria si el brief pide PDF: sin ella no se puede llegar a `APROBADO` |
| Fuentes DejaVu Sans y Sans Mono | Plantilla por defecto | Recomendadas |

Para capturar pantallas hace falta al menos un MCP de navegador: **Playwright** (preferido; `claude mcp add playwright npx '@playwright/mcp@latest'`), **Chrome DevTools** (si se necesita la sesión real del usuario) o **Puppeteer**. Sin ninguno, el plugin genera `capturas/INSTRUCCIONES.md` para captura manual.

## Seguridad de la compilación

El Markdown lo redactan agentes y no es de confianza, así que la compilación es fail-closed:

- Rechaza (rc 2) imágenes remotas, fuera del manual o con esquemas no permitidos, y enlaces con esquemas ejecutables como `javascript:`.
- Desactiva TeX crudo y matemáticas `$…$` en todos los formatos (las matemáticas salen como texto literal).
- El PDF rechaza enlaces simbólicos (rc 6); las demás salidas los omiten con aviso.
- Si Typst está instalado y falla, termina con rc 5 sin caer a LaTeX.

Detalle y tabla de códigos de salida en `skills/manual-compiler/SKILL.md`.

## Carpeta de trabajo

Cada manual vive en una carpeta propia del directorio actual:

```
manual-{slug-app}-{YYYY-MM-DD}/              (es)
manual-{slug-app}-{lang}-{YYYY-MM-DD}/       (en, pt)
├── estado.md              progreso y rondas de corrección
├── 01-brief.md
├── 02-plan.md
├── 03-inventario.md
├── capturas/              *.png + MANIFIESTO.md
├── secciones/             00-INDICE.md + {ID}-{slug}.md
├── salida/                manual.{docx,pdf,html,md}, web/ + compilacion.log
└── verificacion.md        (+ verificacion-ronda-N[-completa].md por ronda)
```

## Referencias por tipo de aplicación

`app-analyzer` carga la que corresponda, en `skills/app-analyzer/references/`: `web-app`, `mobile-app`, `desktop-app`, `cms-platform`, `saas-api` y `auth-flows` (en pantallas con DOM los códigos 2FA nunca se capturan: se sustituyen por un valor de ejemplo; en apps móviles y de escritorio esas pantallas se describen con texto).

## Desarrollo

```
python3 -m unittest discover -s tests
claude plugin validate .
claude plugin eval . --no-publish --runs 1 --max-cost-usd 2 --threshold 0.8
```

- `tests/`: compilación, verificadores y enmascarado de datos personales.
- `evals/`: 5 casos (el orquestador se activa con una petición de manual; no se activa con un README técnico; el brainstormer pregunta antes de escribir; el verificador no aprueba sin `manual.docx`; el capturador enmascara datos personales).

## Inspiraciones

- [obra/superpowers](https://github.com/obra/superpowers): workflow socrático por fases con artefactos verificables, subagentes frescos por tarea, evidencia antes de afirmaciones y bucle de corrección acotado.
- [GLINCKER/readme-generator](https://github.com/GLINCKER/claude-code-marketplace/tree/main/skills/documentation/readme-generator): análisis de la app cruzando código y UI.
- [danielrosehill/user-manual-plugin](https://github.com/danielrosehill/user-manual-plugin): compilación modular DOCX/PDF con Typst y fallback a Pandoc.
- [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents): la persona «technical writer senior» del redactor.
- [levnikolaevich/claude-code-skills](https://github.com/levnikolaevich/claude-code-skills): pipeline de documentación sin dependencias pesadas.

## Licencia

MIT. Ver [LICENSE](LICENSE).
