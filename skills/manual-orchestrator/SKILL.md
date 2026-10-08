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
| 6 | Compilación (DOCX, PDF, HTML, Markdown — los que pida `formato` del brief) | `manual-compiler` | `salida/manual.{docx,pdf,html,md}` | No |
| 7 | Verificación de calidad | `manual-verifier` | `verificacion.md` | No (informe se muestra siempre) |

## Opción `--idioma`

`/manual [nombre-app] --idioma es|en|pt` (default `es`, igual que el `idioma` de `01-brief.md`; misma tabla `es`/`en`/`pt` que usa `concatenate.py`, ver `manual-compiler/SKILL.md`). Fija el campo `idioma` del brief que arranca el flujo; no es un flag aparte para cada fase.

- Sin `--idioma`, o `--idioma es`: el nombre de la carpeta NO cambia (`manual-{slug-app}-{YYYY-MM-DD}/`, igual que hoy — compatibilidad).
- Con `--idioma en` o `--idioma pt`: la carpeta pasa a `manual-{slug-app}-{lang}-{YYYY-MM-DD}/`.

### Reutilizar fases 1-3 de otro idioma (flujo, no automatizado)

Si el PO pide explícitamente generar el mismo manual en otro idioma reutilizando el trabajo ya hecho, las fases 1-3 (brainstorm/plan/analyze) se pueden copiar de una corrida previa en vez de rehacerse desde cero:

1. Copiar `01-brief.md`, `02-plan.md` y `03-inventario.md` de la carpeta del idioma de origen a la carpeta nueva (`manual-{slug-app}-{lang}-{YYYY-MM-DD}/`, creada con la fecha de hoy).
2. Actualizar a mano el campo `idioma` de `01-brief.md` al nuevo idioma antes de continuar; **no** tocar nombres de pantallas/elementos de UI del inventario todavía (eso lo hace la fase 3 si la UI real cambia de idioma — ver más abajo).
3. Marcar los tres artefactos como ya aprobados (igual que si el checkpoint humano ya hubiera corrido) y seguir en la fase 4.

Las **fases 4-7 (capture/write/compile/verify) SIEMPRE se rehacen**, nunca se copian: la captura de pantallas debe mostrar la UI real en el idioma nuevo (`screenshot-capturer/SKILL.md:101`, "Idioma de la UI = idioma del manual"; si la app no tiene esa UI en el idioma pedido, es bloqueante, no se simula), y la redacción, compilación y verificación dependen de las capturas y del idioma del texto. Reutilizar brief/plan/inventario ahorra las preguntas de alcance y audiencia (que no cambian con el idioma); no ahorra nada de lo que depende de la UI o de la prosa.

## Directorio de trabajo

Todo el manual vive en una carpeta única para garantizar reproducibilidad y facilitar borrados.

```
manual-{slug-app}-{YYYY-MM-DD}/              (es, o sin --idioma: nombre sin cambios)
manual-{slug-app}-{lang}-{YYYY-MM-DD}/       (--idioma en|pt)
├── estado.md                       (progreso del workflow, ver "Estado del workflow")
├── 00-discovery.md                 (opcional, ver "Discovery preliminar")
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

## Discovery preliminar (excepción a la regla 1)

La regla 1 dice "no saltar fases". Hay **una excepción legítima**: cuando el cliente no domina la terminología propia del producto (no sabe el nombre real del módulo, los roles, los campos, las pantallas), una **inspección preliminar** de Nivel 2/3 puede ejecutarse durante la fase 1 con dos restricciones estrictas:

1. **No sustituye el inventario formal.** Su salida es `00-discovery.md` (notas crudas), nunca `03-inventario.md`. La fase 3 sigue siendo obligatoria y se ejecuta con todas sus reglas.
2. **Sólo informa el brief.** Sirve para responder con datos reales los bloques A/B/C; los hallazgos se traducen en propuestas de respuesta que el usuario confirma.

Casos típicos donde aplicar discovery preliminar:

- El usuario dice "quiero un manual para X" y no sabe los nombres exactos de pantallas / roles / entidades.
- El producto tiene workflows o entidades anidadas (módulos, sub-módulos, plugins de plugin) que el cliente no ha desplegado mentalmente.
- El idioma de la UI puede no coincidir con lo que el cliente recuerda.

El brainstormer registra el resultado del discovery en el campo `discovery_realizado` del `01-brief.md` con fecha y nivel de inspección. Si no hubo discovery, el campo es `false`.

- `slug-app` se deriva del nombre comercial recogido en la fase 1, en kebab-case ASCII (sin acentos ni espacios).
- `YYYY-MM-DD` es la fecha local del día en que arranca el flujo. No cambia durante la ejecución.
- Si la carpeta ya existe, ofrecer al usuario continuar (reusa los artefactos existentes, retomando según `estado.md`) o empezar de cero (renombra la anterior con sufijo `.bak-{HHMMSS}`).

## Estado del workflow

`estado.md` vive en la carpeta de **este** manual (nunca global ni compartida entre manuales) y es el mapa de recuperación si la sesión se interrumpe o se compacta. El orquestador lo actualiza al cerrar cada fase y cada ronda de corrección, en el mismo turno.

- Primera línea: `# Estado — manual-{slug-app}-{YYYY-MM-DD}`. Si al continuar la primera línea nombra otra carpeta, no es el estado de este manual: ignorarlo.
- Una línea por hito, sin prosa: `Fase 3: completa (03-inventario.md, aprobada por el usuario)`, `Fase 7: ronda 2/5 acotada (3 cerrados, 1 abierto — C2; cambió: fase 4 re-ejecutada para S07; falló: captura sin resaltado; ver verificacion-ronda-2.md)`. La línea de ronda lleva siempre «cambió» y «falló» (mínimo para que la ronda siguiente sepa lo intentado).
- Al continuar, retomar en la primera fase sin línea `completa`; una fase con última línea de ronda está en medio del bucle de corrección: seguir en la ronda siguiente.
- Si `estado.md` y los artefactos discrepan, mandan los artefactos (regla 2): reverificar el artefacto y corregir el estado.

## Reglas de transición entre fases

Antes de delegar a la skill de la fase N, verificar:

1. Existe el artefacto principal de la fase N-1 (archivo presente y no vacío).
2. El artefacto contiene la estructura mínima esperada (validar con un grep simple del campo más distintivo: por ejemplo, `audiencia:` en `01-brief.md`).
3. Si el artefacto está marcado como `borrador: true` en su frontmatter, no avanzar.

Si alguna verificación falla, **no invocar la skill siguiente**. Mostrar al usuario qué falta y devolver el flujo a la fase pendiente.

## Comandos disponibles

| Comando | Efecto |
|---------|--------|
| `/manual [nombre-app] [--idioma es\|en\|pt]` | Workflow completo de 7 fases (idioma del manual; default `es`, ver "Opción `--idioma`") |
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
2. Veredicto final del verificador (`APROBADO` / `BLOQUEADO`; `PENDIENTE-PASADA-COMPLETA` es intermedio y siempre dispara la pasada completa del paso 5 del bucle, nunca se muestra como final).
3. Rutas absolutas de los artefactos de `salida/` que el brief pidió (`manual.docx`, `manual.pdf`, `manual.html`, `manual.md`) que estén presentes.
4. Lista de advertencias no bloqueantes que el usuario debería revisar manualmente.

Si el veredicto es `BLOQUEADO`, no afirmar que el manual está terminado. Indicar exactamente qué check falló y qué fase debe re-ejecutarse, y entrar en el bucle de corrección.

## Bucle de corrección tras `BLOQUEADO`

Una **ronda** = una corrección acotada + una re-verificación acotada. Máximo **5 rondas** por manual. Numeración: la verificación inicial (`verificacion.md` tras la fase 7) es la **ronda 0**; la ronda N es la que sigue a la N-ésima corrección. Este contador es independiente del límite de 3 iteraciones por sección de `manual-writer` (que ocurre antes de aceptar un borrador).

1. **Corrección acotada.** Re-ejecutar solo la fase que el informe señala y solo sobre lo afectado (las secciones o capturas citadas, no el manual entero), pasando los hallazgos del informe textuales. Luego re-ejecutar las fases posteriores que consumen lo cambiado (típicamente la 6). El orquestador no corrige contenido él mismo: delega a la skill de la fase.
2. **Mismo ejecutor en las rondas 1-3.** Reanudar el subagente que redactó o capturó lo afectado, que conserva el contexto de lo que hizo; si no puede reanudarse, uno fresco con los hallazgos y el estado. En las rondas 4-5, un subagente fresco que reciba lo intentado (las líneas de ronda de `estado.md` y los `verificacion-ronda-N.md`): un fallo que sobrevive a tres rondas suele ser un error de enfoque, no de detalle.
3. **Re-verificación acotada.** Invocar `manual-verifier` indicando la ronda, los hallazgos abiertos y los archivos cambiados (sección "Re-verificación tras una corrección" del verificador). Un hallazgo nuevo en lo que cambió entra en la lista abierta; una observación sobre lo no tocado, si es de un check no bloqueante, se anota como advertencia y no alarga el bucle; si es de un check bloqueante, se registra como «pendiente para la pasada completa» (no se degrada a advertencia). Al terminar cada ronda N, copiar `verificacion.md` a `verificacion-ronda-N.md` (se conserva uno por ronda; el inicial queda como ronda 0).
4. **Registro.** Añadir a `estado.md` la línea de la ronda antes de la siguiente, con qué se cambió y por qué falló (formato en «Estado del workflow»).
5. **Cierre.** Una re-verificación acotada sin bloqueantes abiertos devuelve `PENDIENTE-PASADA-COMPLETA` (no es `APROBADO`): invocar entonces al verificador para una pasada completa de todos los checks (`alcance: completa`); solo esa pasada puede emitir `APROBADO`. La pasada completa hereda el `ronda: N` de la ronda en que corre y se guarda como `verificacion-ronda-N-completa.md` para no pisar la acotada. `PENDIENTE-PASADA-COMPLETA` es siempre intermedio: nunca es el estado final. Si la pasada completa falla (incluidos los «pendientes» del paso 3), abre la ronda siguiente con esos hallazgos como lista abierta; si ya se estaba en la ronda 5, cuenta como el corte del paso 6 (no hay ronda 6).
6. **Corte en la ronda 5.** Si tras la ronda 5 (incluida su pasada completa) siguen bloqueantes abiertos, **parar**. Mostrar al usuario los hallazgos abiertos, qué se intentó en cada ronda y la fase que el informe señala, y esperar su decisión (replantear el plan, ajustar el alcance o llevarse los archivos tal cual con el veredicto `BLOQUEADO` a la vista, sin afirmar que el manual está terminado). No iniciar una ronda 6 ni degradar un check bloqueante a advertencia para cerrar.
