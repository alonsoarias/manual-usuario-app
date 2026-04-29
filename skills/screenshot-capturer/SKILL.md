---
name: screenshot-capturer
description: Activar en la fase 4 del workflow de manuales, por el comando /manual-capture, o cuando el usuario pida tomar screenshots, capturas de pantalla, pantallazos o imágenes de una aplicación. Requiere 02-plan.md y 03-inventario.md presentes.
---

# Skill: screenshot-capturer

Fase 4 del workflow. Convierte la lista de capturas requeridas del plan en archivos PNG físicos. Es la skill que conecta al plugin con las herramientas MCP disponibles en el entorno del usuario, con detección automática y fallbacks ordenados.

## Pre-requisito (regla 1)

Verificar que existen `02-plan.md` y `03-inventario.md` con `borrador: false`. Si no, **abortar** y devolver a la fase pendiente.

## Detección de herramienta (orden de preferencia)

La skill prueba en este orden y usa la primera disponible:

### 1. Playwright MCP (preferida)

Tools típicas: `browser_navigate`, `browser_take_screenshot`, `browser_snapshot`, `browser_click`, `browser_fill_form`, `browser_type`, `browser_resize`, `browser_wait_for`, `browser_evaluate`, `browser_press_key`.

Detectar por la presencia de tools con prefijo `mcp__playwright__browser_*` o `mcp__plugin_playwright_playwright__browser_*`.

Si no está instalada y el usuario tiene Claude Code, sugerir:

```
claude mcp add playwright npx '@playwright/mcp@latest'
```

Consultar `references/playwright-mcp.md` para flujos completos de captura.

### 2. Chrome DevTools MCP

Tools típicas: `list_pages`, `select_page`, `navigate_page`, `take_screenshot`, `evaluate_script`.

Requiere Chrome arrancado con `--remote-debugging-port=9222`. Útil cuando el usuario quiere capturar **su sesión real** (cookies, extensiones, datos ya cargados) sin re-autenticarse.

Consultar `references/chrome-devtools-mcp.md`.

### 3. Puppeteer MCP

Tools con prefijo `mcp__puppeteer__*`. Funcionalidad similar a Playwright pero típicamente con menos cobertura de tools.

### 4. CLI bash

Si no hay MCP de browser disponible, intentar:

- `npx playwright screenshot {url} {salida.png} --viewport-size=1366,768`
- `chromium --headless --disable-gpu --screenshot={salida.png} --window-size=1366,768 {url}`
- `wkhtmltoimage {url} {salida.png}`
- En plataformas CMS con rutas internas, considerar `curl` para verificar disponibilidad antes de lanzar el navegador.

### 5. Fallback manual

Cuando ninguna automatización es viable (apps móviles sin emulador, escritorio sin acceso, sitio detrás de auth complejo) generar `capturas/INSTRUCCIONES.md` con un bloque por captura listada en el plan.

Consultar `references/manual-capture-fallback.md`.

## Convenciones de nombre

Los nombres de archivo siguen exactamente el formato declarado en `02-plan.md` por el planner:

```
{ID-seccion}-{descripcion-kebab}.png
```

Ejemplos:

- `S03-pantalla-login.png`
- `S03-pantalla-login-error.png`
- `S05-dashboard-vacio.png`
- `S05-dashboard-con-datos.png`

Si el plan declaró un nombre, **no improvisar otro**. Si la captura no existe en el plan, no producirla.

## Convenciones de captura

### Viewport

Heredar del plan (`ambiente_capturas`). Por defecto:

| Tipo de app | Viewport |
|-------------|----------|
| Web desktop | 1366x768 |
| Web móvil | 375x812 (iPhone) o 412x915 (Android) |
| Escritorio | resolución de la ventana principal, recortada al borde |

### Estado de la app

- **Sin datos personales reales.** Si la app contiene información de personas concretas, el `screenshot-capturer` debe poblar el ambiente con datos sintéticos antes de capturar, o pedir al cliente un ambiente de demo. Nunca capturar datos reales sin autorización explícita.
- **Idioma de la UI = idioma del manual.** Si el ambiente está en otro idioma, cambiarlo o reportar como bloqueante.
- **Estado limpio.** Para tareas que empiezan desde cero, capturar antes de cualquier interacción. Para flujos parciales, reproducir el estado mínimo necesario.
- **Sin notificaciones del SO.** Cerrar toasts, banners y modales no relacionados antes de capturar.
- **Modo claro u oscuro consistente.** El que declare el cliente; por defecto, el modo claro suele leerse mejor en impresión.

### Dimensiones físicas

- Ancho mínimo: 1024 px (1366 ideal).
- Densidad: 1x recomendable; 2x sólo si el manual se imprimirá en alta resolución.
- Formato: PNG.
- Compresión: por defecto sin pérdida; para reducir tamaño, usar `pngquant` con `--quality=85-95`.

## Anotaciones

Cuando la captura requiere flechas, números o resaltados según el plan:

### Opción A — Inyección con `browser_evaluate` (preferida)

Antes de capturar, inyectar overlays CSS con JavaScript:

```js
// Ejemplo: numerar elementos del DOM
document.querySelectorAll('button').forEach((el, i) => {
  const dot = document.createElement('div');
  dot.textContent = String(i + 1);
  dot.style.cssText = 'position:absolute;background:#ff5722;color:#fff;border-radius:50%;width:24px;height:24px;display:flex;align-items:center;justify-content:center;font:bold 14px sans-serif;z-index:9999';
  const r = el.getBoundingClientRect();
  dot.style.top = (window.scrollY + r.top - 12) + 'px';
  dot.style.left = (window.scrollX + r.left - 12) + 'px';
  document.body.appendChild(dot);
});
```

Ventaja: anotaciones a resolución nativa, sin re-procesado de imagen.

### Opción B — Post-proceso con Pillow (Python)

Si la inyección no es viable, anotar la imagen final con Pillow usando coordenadas declaradas en el plan o detectadas heurísticamente.

### Opción C — Anotación manual

En el fallback manual, instruir al usuario sobre qué anotar y con qué herramienta. No imponer software específico.

## Workflow de la skill

1. Leer `02-plan.md` → extraer todas las capturas requeridas con sus IDs y nombres exactos.
2. Leer `03-inventario.md` → identificar las URLs/pantallas a navegar y los pasos previos (login, llenar formularios, etc.).
3. Detectar la herramienta disponible (orden 1-5).
4. Para cada captura del plan:
   1. Navegar a la pantalla (con login previo si la pantalla está autenticada).
   2. Llenar formularios o disparar el estado declarado.
   3. Esperar que termine el render (`browser_wait_for`, `await page.waitForLoadState('networkidle')`, etc.).
   4. Aplicar anotaciones si el plan las pide.
   5. Capturar con el viewport declarado.
   6. Guardar con el nombre exacto del plan.
5. Verificar que **todos** los archivos PNG del plan existen en `capturas/`.
6. Generar `capturas/MANIFIESTO.md` con la lista verificada.
7. Si quedan capturas pendientes, generar `capturas/INSTRUCCIONES.md` con sus pasos manuales y reportar al usuario qué falta.

## Salida obligatoria: `capturas/MANIFIESTO.md`

```markdown
---
total_planificadas: N
total_producidas: M
producidas_automaticamente: A
producidas_manualmente: B
herramienta: "playwright-mcp | chrome-devtools-mcp | puppeteer-mcp | cli-playwright | cli-chromium | manual"
viewport: "1366x768"
fecha: "YYYY-MM-DD HH:MM"
---

# Manifiesto de capturas

| Archivo | Sección | Tamaño px | Estado | Herramienta | Anotaciones |
|---------|---------|-----------|--------|-------------|-------------|
| S03-pantalla-login.png | S03 | 1366x768 | OK | playwright-mcp | sí |
| S03-pantalla-login-error.png | S03 | 1366x768 | OK | playwright-mcp | sí |
| S05-dashboard-vacio.png | S05 | 1366x768 | PENDIENTE-MANUAL | manual | n/a |
```

## Validaciones antes de cerrar la fase

- Cada captura listada en el plan tiene su archivo o una entrada `PENDIENTE-MANUAL` en el manifiesto.
- Cada PNG existente cumple el viewport declarado en ±5%.
- No hay PNGs huérfanos (presentes en `capturas/` pero no en el plan): si los hay, listar y preguntar antes de borrar.
- Si hay capturas pendientes manuales, informar al usuario y no avanzar a la fase 5 sin confirmación explícita.

## Anti-patrones

- Capturar pantallas no listadas en el plan "por si acaso".
- Renombrar archivos para que "queden mejor": el plan manda.
- Subir capturas con datos reales de usuarios sin autorización.
- Capturar a resolución 800x600 cuando el plan pide 1366x768.
- Mezclar idiomas (UI en inglés, manual en español).
- Saltarse el manifiesto.
