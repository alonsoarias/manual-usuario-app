# Captura con Chrome DevTools MCP

Guía operativa para usar Chrome DevTools MCP cuando es preferible sobre Playwright. Este flujo es útil cuando el usuario quiere capturar **su sesión real** del navegador (cookies, extensiones, datos cargados, configuraciones personalizadas) sin re-autenticarse en un navegador limpio.

## Cuándo elegirlo sobre Playwright

| Escenario | Mejor opción |
|-----------|--------------|
| Captura de sitio público | Playwright |
| Login complejo con MFA o SSO | Chrome DevTools (usa la sesión existente) |
| Sitio que requiere extensiones del navegador | Chrome DevTools |
| Sitio con autenticación por certificado de cliente | Chrome DevTools |
| Captura de DevTools en sí (pestaña Network, Console, etc.) | Chrome DevTools |
| Captura de comportamiento que depende del perfil del usuario | Chrome DevTools |
| Pipeline reproducible automatizado | Playwright |

## Tools típicas

| Tool | Propósito |
|------|-----------|
| `list_pages` | Listar pestañas abiertas en el Chrome conectado |
| `select_page` | Apuntar a una pestaña por id o URL |
| `navigate_page` | Navegar la pestaña seleccionada a una URL |
| `take_screenshot` | Capturar PNG de la pestaña activa |
| `evaluate_script` | Ejecutar JavaScript en el contexto de la pestaña |
| `click_element` | Click en un selector CSS |
| `fill_input` | Rellenar un input |

(Los nombres exactos pueden variar entre implementaciones; la API expuesta sigue el protocolo CDP / Chrome DevTools Protocol.)

## Pre-requisito: Chrome con remote debugging

El usuario debe arrancar Chrome con la flag `--remote-debugging-port=9222` y un perfil dedicado (recomendado para no contaminar el perfil principal).

### Linux

```
google-chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug \
  --no-first-run \
  &
```

### macOS

```
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug \
  --no-first-run &
```

### Windows (PowerShell)

```
& "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  --remote-debugging-port=9222 `
  --user-data-dir=$env:TEMP\chrome-debug `
  --no-first-run
```

### Verificación

Tras arrancar Chrome, abrir `http://localhost:9222/json/version` en otra pestaña o con `curl`. Debe devolver un JSON con la versión y `webSocketDebuggerUrl`.

## Flujo típico

### Flujo A — Capturar pestaña ya abierta

El usuario ya navegó a la pantalla deseada, hizo login y dejó la app en el estado correcto.

```
list_pages                                    # listar pestañas y sus URLs
select_page         { id: "{id-pagina}" }     # apuntar a la pestaña
take_screenshot     { filename: "S05-dashboard.png", fullPage: false }
```

### Flujo B — Navegar y capturar dentro de la sesión existente

```
list_pages
select_page         { id: "{id-pagina}" }
navigate_page       { url: "https://app.cliente.com/configuracion" }
evaluate_script     { code: "document.title" }                    # esperar a que cargue
take_screenshot     { filename: "S08-configuracion.png" }
```

### Flujo C — Inyectar anotaciones antes de capturar

Funciona igual que en Playwright (ver `playwright-mcp.md`):

```
evaluate_script  { code: "/* JavaScript de overlays */" }
take_screenshot  { filename: "S03-paso-anotado.png" }
evaluate_script  { code: "document.querySelectorAll('.overlay-screenshot').forEach(e => e.remove())" }
```

## Ventajas de Chrome DevTools MCP

- **Sesión real del usuario**: cookies de SSO, sesiones MFA ya iniciadas, autenticación por certificado.
- **Extensiones activas**: si el manual documenta una integración con una extensión específica, sólo este modo la captura.
- **Multi-pestaña**: capturar varias pantallas mantenidas abiertas en paralelo.
- **Sin re-autenticación**: ahorra tiempo en sitios con login complejo.

## Desventajas

- **Reproducibilidad baja**: la pestaña depende del estado que el usuario haya dejado. Para pipelines automatizados (CI/CD), preferir Playwright.
- **Riesgo de capturar datos personales del usuario**: la sesión real puede contener información que no debe aparecer en el manual. Antes de capturar, sanear (cerrar sesión, cambiar a perfil demo, anonimizar con `evaluate_script`).
- **Requiere intervención manual**: arrancar Chrome con la flag de debug es un paso adicional.
- **Menos tools que Playwright**: cobertura más limitada para interacciones complejas (drag-drop, file upload).

## Saneamiento previo a capturar

Antes de cada captura desde la sesión real del usuario, ejecutar un check rápido:

```js
// evaluate_script
(() => {
  // Cambiar nombres y emails visibles a placeholders
  document.querySelectorAll('[data-user-name], .user-name').forEach(el => el.textContent = 'Usuario Demo');
  document.querySelectorAll('[data-user-email], .user-email').forEach(el => el.textContent = 'demo@example.com');
  // Ocultar avatares que sean fotos reales
  document.querySelectorAll('img.avatar, .avatar img').forEach(el => el.style.visibility = 'hidden');
  return 'sanitizado';
})()
```

Adaptar selectores al inventario de la app concreta.

## Cuándo no usar Chrome DevTools MCP

- Cuando se requiera capturar de manera 100% automatizada y sin interacción del usuario.
- Cuando la app sea móvil o de escritorio (no hay browser).
- Cuando el cliente pida capturas de un ambiente de demo sin cookies/cuentas reales.

## Combinación con Playwright

Es legítimo usar ambos en el mismo flujo:

- Playwright para la mayoría de las capturas, en ambiente de demo.
- Chrome DevTools para capturas específicas que requieren una sesión real (p. ej. integración SSO con identity provider del cliente).

En ese caso, el manifiesto registra la herramienta usada por captura.
