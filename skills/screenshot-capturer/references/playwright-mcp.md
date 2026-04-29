# Captura con Playwright MCP

Guía operativa para usar Playwright MCP como herramienta principal de captura. Este es el camino preferido cuando esté disponible.

## Tools disponibles

Las tools de Playwright MCP siguen el patrón `mcp__playwright__browser_*` (o `mcp__plugin_playwright_playwright__browser_*` cuando se distribuye vía plugin de Claude Code).

| Tool | Propósito |
|------|-----------|
| `browser_navigate` | Cargar una URL |
| `browser_navigate_back` | Volver atrás en el historial |
| `browser_resize` | Cambiar el viewport |
| `browser_take_screenshot` | Capturar PNG de la página o de un elemento |
| `browser_snapshot` | Snapshot de accesibilidad (texto del DOM) — útil para validar contenido |
| `browser_click` | Click en un elemento |
| `browser_hover` | Pasar el ratón por encima |
| `browser_fill_form` | Rellenar campos de un formulario |
| `browser_type` | Escribir texto en un input |
| `browser_press_key` | Pulsar una tecla |
| `browser_select_option` | Elegir opción de un `<select>` |
| `browser_drag` / `browser_drop` | Arrastrar y soltar |
| `browser_wait_for` | Esperar a que aparezca/desaparezca un texto o elemento |
| `browser_evaluate` | Ejecutar JavaScript en el contexto de la página |
| `browser_console_messages` | Leer la consola del navegador |
| `browser_network_requests` | Inspeccionar peticiones de red |
| `browser_handle_dialog` | Aceptar/cancelar diálogos nativos |
| `browser_file_upload` | Subir archivos en inputs `type=file` |
| `browser_tabs` | Listar y conmutar pestañas |
| `browser_close` | Cerrar el navegador |

## Flujos típicos

### Flujo 1 — Captura simple de pantalla pública

```
browser_navigate          { url: "https://app.cliente.com" }
browser_resize            { width: 1366, height: 768 }
browser_wait_for          { text: "Bienvenido" }
browser_take_screenshot   { filename: "S02-portada-publica.png", fullPage: false }
```

### Flujo 2 — Pantalla autenticada (login + captura)

```
browser_navigate          { url: "https://app.cliente.com/login" }
browser_fill_form         { fields: [
                              { name: "Correo electrónico", type: "textbox", value: "demo@example.com" },
                              { name: "Contraseña", type: "textbox", value: "demo-password" }
                          ] }
browser_click             { element: "botón Ingresar", ref: "..." }
browser_wait_for          { text: "Panel principal" }
browser_take_screenshot   { filename: "S05-dashboard-principal.png" }
```

### Flujo 3 — Captura de error de validación

```
browser_navigate          { url: "https://app.cliente.com/login" }
browser_click             { element: "botón Ingresar", ref: "..." }
browser_wait_for          { text: "El campo correo electrónico es obligatorio" }
browser_take_screenshot   { filename: "S03-login-error-validacion.png" }
```

### Flujo 4 — Captura en viewport móvil

```
browser_resize            { width: 375, height: 812 }
browser_navigate          { url: "https://app.cliente.com" }
browser_wait_for          { time: 1 }
browser_take_screenshot   { filename: "S04-vista-movil.png" }
```

## Inyección de overlays con `browser_evaluate`

Antes de capturar, ejecutar JavaScript que añada decoraciones al DOM. La captura las verá como parte de la página.

### Numerar pasos de un formulario

```js
const fields = ['email', 'password', 'submit'];
fields.forEach((sel, i) => {
  const el = document.querySelector(`[name="${sel}"], button[type="submit"]`);
  if (!el) return;
  const r = el.getBoundingClientRect();
  const tag = document.createElement('div');
  tag.textContent = i + 1;
  Object.assign(tag.style, {
    position: 'absolute',
    top: (window.scrollY + r.top - 14) + 'px',
    left: (window.scrollX + r.left - 14) + 'px',
    width: '28px', height: '28px',
    background: '#ff5722', color: '#fff',
    borderRadius: '50%',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    font: 'bold 14px sans-serif',
    zIndex: 99999,
    boxShadow: '0 2px 4px rgba(0,0,0,.3)'
  });
  document.body.appendChild(tag);
});
```

### Resaltar un elemento con borde

```js
const el = document.querySelector('button.primary');
if (el) {
  el.style.outline = '3px solid #ff5722';
  el.style.outlineOffset = '2px';
}
```

### Tachar datos sensibles antes de capturar

```js
document.querySelectorAll('[data-private]').forEach(el => {
  el.style.background = '#000';
  el.style.color = '#000';
});
```

### Sanear nombres y emails reales en `<select>` y listas

Las apps administrativas suelen poblar selects con nombres y emails reales de usuarios del cliente. Antes de capturar la pantalla con un select desplegado o una lista de personas, reemplazar esos valores por placeholders genéricos:

```js
(() => {
  // Patrones de PII frecuentes en UIs en español
  const emailRegex = /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g;
  // Reemplazo nombre+email en options de <select>
  document.querySelectorAll('select option').forEach((opt, i) => {
    if (i === 0) return; // dejar la primera (placeholder "Seleccione...")
    opt.textContent = `Usuario de ejemplo ${i} (usuario${i}@example.com)`;
  });
  // Reemplazo en celdas de tablas con emails visibles
  document.querySelectorAll('td, span, div').forEach(el => {
    if (el.children.length === 0 && emailRegex.test(el.textContent)) {
      el.textContent = el.textContent.replace(emailRegex, 'usuario@example.com');
    }
  });
  // Reemplazo de nombres propios visibles (heurística: dos+ palabras capitalizadas seguidas)
  // Aplicar SÓLO en zonas marcadas, no globalmente, para no romper la UI
  document.querySelectorAll('[data-user-name], .user-name, .userpicture + .username').forEach((el, i) => {
    el.textContent = `Usuario Demo ${i + 1}`;
  });
  return 'sanitizado';
})()
```

Aplicarlo **antes** de capturar y, si el manual sigue siendo editable después, recargar la página para volver al estado real.

#### Cuándo es obligatorio

- Selects de "Asignar usuario / rol" con la lista de personas del cliente.
- Tablas con columnas "Creado por", "Asignado a", "Email", "Identificación".
- Cualquier captura tras login con "Bienvenido, {nombre real}" en el header.

El plan de la fase 2 declara esta necesidad marcando la captura con anotación `tachado-datos`. La skill nunca decide tachar por su cuenta sin que el plan lo declare.

## Validar el contenido antes de capturar

`browser_snapshot` produce el árbol de accesibilidad. Útil para confirmar que la página llegó al estado esperado:

```
browser_snapshot          # devuelve estructura textual
```

Buscar en la respuesta el texto exacto inventariado en la fase 3. Si no aparece, no capturar: la página no está en el estado pedido.

## Manejo de elementos asíncronos

Patrones comunes:

| Situación | Estrategia |
|-----------|-----------|
| Spinner que aparece y desaparece | `browser_wait_for { textGone: "Cargando..." }` |
| Toast que aparece tras una acción | `browser_wait_for { text: "Guardado correctamente" }` antes de capturar |
| Animaciones CSS | `browser_evaluate { code: "document.body.style.animation='none'" }` para deshabilitarlas |
| Datos cargados vía fetch | `browser_wait_for { time: 2 }` o esperar texto específico que sólo aparece tras carga |

## Cookies y estado pre-cargado

Para evitar repetir login en cada captura:

1. Hacer login una vez al inicio.
2. Las cookies persisten dentro de la sesión del MCP mientras no se cierre el navegador.
3. Si la sesión expira, repetir login.

Para escenarios donde el cliente provee `storageState.json`:

```
browser_evaluate          { code: "// no aplicable, requiere config externa de Playwright" }
```

## Limitaciones de Playwright MCP

- No captura el cromo del SO (sólo el área del browser); para mostrar la barra de URL u otros elementos de Chrome, usar `chrome-devtools-mcp.md` o capturar con la herramienta del SO.
- No interactúa con extensiones del navegador.
- Cada sesión arranca con un perfil limpio: para usar el perfil del usuario, ver `chrome-devtools-mcp.md`.
- Carga páginas más lento que un navegador real cuando hay mucho JavaScript: usar `browser_wait_for` antes que `browser_take_screenshot`.

## Patrón recomendado por captura

Estructura que el `screenshot-capturer` debería seguir para cada entrada del plan:

1. Verificar que existe el bloque de pasos en el inventario (Regla 1: si no hay evidencia de cómo llegar a la pantalla, abortar).
2. Navegar a la URL inicial.
3. Ejecutar los pasos previos del inventario (login, llenar campos, navegar a sub-vista).
4. Esperar el estado verificable (texto inventariado).
5. Aplicar anotaciones si el plan las pide.
6. Capturar con viewport y nombre del plan.
7. Validar tamaño del PNG (≥ 50 KB y ≤ 5 MB; valores fuera de rango = sospechoso).
8. Anotar resultado en el manifiesto.
