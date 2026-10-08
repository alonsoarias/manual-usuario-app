---
description: Genera un manual de usuario completo de una aplicación, ejecutando las 7 fases en secuencia con checkpoints después de las fases 1, 2 y 3. Acepta el flag --rapido para omitir checkpoints intermedios (la fase 7 siempre se ejecuta) y --idioma es|en|pt para fijar el idioma del manual (default es).
argument-hint: "[nombre-app] [--rapido] [--idioma es|en|pt]"
---

# Generación completa de manual de usuario

Aplicación a documentar: **$ARGUMENTS**

Usa la skill `manual-orchestrator` para coordinar las 7 fases del workflow. La orquestadora delega cada fase a su skill especializada y verifica el artefacto producido antes de avanzar.

## Las 7 fases

1. **Brainstorming socrático** → skill `manual-brainstormer` → `01-brief.md` (checkpoint)
2. **Plan de secciones** → skill `manual-planner` → `02-plan.md` (checkpoint)
3. **Análisis de la aplicación** → skill `app-analyzer` → `03-inventario.md` (checkpoint)
4. **Captura de pantallas** → skill `screenshot-capturer` → `capturas/*.png` + `MANIFIESTO.md`
5. **Redacción por subagentes** → skill `manual-writer` → `secciones/*.md`
6. **Compilación** → skill `manual-compiler` → los formatos que pida `01-brief.md` (`salida/manual.docx`, `salida/manual.pdf`, `salida/manual.html`, `salida/manual.md`)
7. **Verificación de calidad** → skill `manual-verifier` → `verificacion.md`

## Reglas innegociables (codificadas en cada skill)

1. **No saltar fases.** Cada fase produce un artefacto que la siguiente verifica.
2. **Evidencia antes de afirmaciones.** La fase 7 siempre se ejecuta y su informe se muestra completo.
3. **YAGNI documental.** No se documenta lo que la app no tiene ni lo que el cliente no usa.

## Modo rápido

Si los argumentos incluyen `--rapido`:

- Las fases 1, 2 y 3 producen sus artefactos sin pedir aprobación humana entre etapas.
- Se aplican defaults: profundidad estándar, formato DOCX+PDF, viewport desktop 1366x768.
- **La fase 7 se ejecuta siempre** y bloquea la entrega si encuentra fallos críticos.

## Opción `--idioma`

`--idioma es|en|pt` (default `es`). Fija el `idioma` de `01-brief.md`. Con `en`/`pt` la carpeta del manual se llama `manual-{slug-app}-{lang}-{YYYY-MM-DD}/` (sin el flag, o con `es`, el nombre no cambia). Las fases 1-3 se pueden reutilizar de una corrida previa en otro idioma si el PO lo pide explícitamente; las fases 4-7 siempre se rehacen porque la UI capturada y el texto redactado deben estar en el idioma del manual. Detalle del flujo: `manual-orchestrator/SKILL.md`, sección "Opción `--idioma`".

## Salida

Una carpeta `manual-{slug-app}-{YYYY-MM-DD}/` (o `manual-{slug-app}-{lang}-{YYYY-MM-DD}/` con `--idioma en|pt`) en el directorio actual con todos los artefactos del workflow. Al terminar, el orquestador reporta:

- Estado de cada fase (✓ / ✗).
- Veredicto final del verificador (`APROBADO` / `BLOQUEADO`). `PENDIENTE-PASADA-COMPLETA` es intermedio: siempre dispara la pasada completa y nunca es el estado final.
- Rutas absolutas de los artefactos de `salida/` producidos (docx/pdf/html/md, según lo que pidió el brief).
- Lista de advertencias no bloqueantes para revisión humana.

Si el veredicto es `BLOQUEADO`, el orquestador indica qué check falló y entra en el bucle de corrección (máx. 5 rondas; si sigue bloqueado, para y pregunta al usuario).
