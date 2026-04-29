---
name: manual-orchestrator
description: Activar cuando el usuario pida crear, generar, redactar o producir un manual de usuario, guía de usuario, manual de uso, instructivo, user manual, user guide o end-user documentation de cualquier aplicación de software (web, móvil, escritorio o CMS).
---

# Skill: manual-orchestrator

Coordina la generación end-to-end de un manual de usuario profesional. No redacta contenido por sí mismo: invoca a las skills especializadas en orden estricto, verifica el artefacto producido por cada fase y decide cuándo pedir confirmación al usuario.

## Tres reglas innegociables

Estas tres reglas se aplican a **todas** las skills de este plugin. Cualquier skill que detecte una infracción debe abortar y devolver el control al orquestador.

### Regla 1 — No saltar fases

Cada fase produce un artefacto que la siguiente consume. Si el artefacto previo no existe o está incompleto, **abortar y devolver a la fase anterior**. Nunca empezar la fase N sin tener el artefacto de la fase N-1.

### Regla 2 — Evidencia antes de afirmaciones

Nunca declarar "manual terminado", "fase completada" o cualquier afirmación de éxito sin haber ejecutado y mostrado la verificación correspondiente. La fase 7 es obligatoria y debe ejecutarse incluso en modo rápido.

### Regla 3 — YAGNI documental

No documentar funcionalidades que la aplicación no tiene. No documentar funcionalidades que la aplicación tiene pero que el cliente final no usa. No incluir secciones por completar el formato. Si una sección no aporta valor al perfil de audiencia definido en la fase 1, eliminarla.

## Las 7 fases del workflow

| # | Fase | Skill responsable | Artefacto producido | Checkpoint humano |
|---|------|-------------------|---------------------|-------------------|
| 1 | Brainstorming socrático | `manual-brainstormer` | `01-brief.md` | Sí |
| 2 | Plan de secciones | `manual-planner` | `02-plan.md` | Sí |
| 3 | Análisis de la aplicación | `app-analyzer` | `03-inventario.md` | Sí |
| 4 | Captura de pantallas | `screenshot-capturer` | `capturas/*.png` + `MANIFIESTO.md` | No |
| 5 | Redacción por subagentes | `manual-writer` | `secciones/*.md` | No |
| 6 | Compilación DOCX/PDF | `manual-compiler` | `salida/manual.{docx,pdf}` | No |
| 7 | Verificación de calidad | `manual-verifier` | `verificacion.md` | No (informe se muestra siempre) |

## Directorio de trabajo

Todo el manual vive en una carpeta única para garantizar reproducibilidad y facilitar borrados.

```
manual-{slug-app}-{YYYY-MM-DD}/
├── 01-brief.md
├── 02-plan.md
├── 03-inventario.md
├── capturas/
│   ├── MANIFIESTO.md
│   ├── INSTRUCCIONES.md            (sólo si hubo fallback manual)
│   └── *.png
├── secciones/
│   └── {ID}-{slug}.md              (una por sección del plan)
├── salida/
│   ├── manual.docx
│   └── manual.pdf
└── verificacion.md
```

- `slug-app` se deriva del nombre comercial recogido en la fase 1, en kebab-case ASCII (sin acentos ni espacios).
- `YYYY-MM-DD` es la fecha local del día en que arranca el flujo. No cambia durante la ejecución.
- Si la carpeta ya existe, ofrecer al usuario continuar (reusa los artefactos existentes) o empezar de cero (renombra la anterior con sufijo `.bak-{HHMMSS}`).

## Reglas de transición entre fases

Antes de delegar a la skill de la fase N, verificar:

1. Existe el artefacto principal de la fase N-1 (archivo presente y no vacío).
2. El artefacto contiene la estructura mínima esperada (validar con un grep simple del campo más distintivo: por ejemplo, `audiencia:` en `01-brief.md`).
3. Si el artefacto está marcado como `borrador: true` en su frontmatter, no avanzar.

Si alguna verificación falla, **no invocar la skill siguiente**. Mostrar al usuario qué falta y devolver el flujo a la fase pendiente.

## Comandos disponibles

| Comando | Efecto |
|---------|--------|
| `/manual [nombre-app]` | Workflow completo de 7 fases |
| `/manual-brainstorm` | Sólo fase 1 |
| `/manual-plan` | Sólo fase 2 |
| `/manual-analyze` | Sólo fase 3 |
| `/manual-capture` | Sólo fase 4 |
| `/manual-write` | Sólo fase 5 |
| `/manual-compile` | Sólo fase 6 |
| `/manual-verify` | Sólo fase 7 |

Cada comando aislado verifica los pre-requisitos antes de ejecutar (regla 1).

## Modo rápido

Si el usuario pasa el flag `--rapido` al comando `/manual`, omitir los checkpoints humanos de las fases 1, 2 y 3. **La fase 7 siempre se ejecuta** (regla 2). En modo rápido también se aplican defaults: profundidad estándar, formato DOCX+PDF, ambiente desktop 1366x768.

## Checkpoint humano

Después de las fases 1, 2 y 3 mostrar al usuario el artefacto producido y pedir explícitamente:

- "Aprobado, continuar con la siguiente fase"
- "Necesita ajustes" (devolver a la skill de la fase actual)
- "Cancelar"

No avanzar sin respuesta del usuario, salvo en modo rápido.

## Salida final del orquestador

Al terminar la fase 7, mostrar:

1. Tabla resumen de las 7 fases con estado (✓ / ✗).
2. Veredicto del verificador (`APROBADO` / `BLOQUEADO`).
3. Rutas absolutas de `manual.docx` y `manual.pdf` si están presentes.
4. Lista de advertencias no bloqueantes que el usuario debería revisar manualmente.

Si el veredicto es `BLOQUEADO`, no afirmar que el manual está terminado. Indicar exactamente qué check falló y qué fase debe re-ejecutarse.
