# Captura manual (fallback)

Guía para cuando ninguna herramienta automatizada está disponible: app móvil sin emulador, escritorio sin acceso, sitio detrás de auth compleja sin Chrome con debug, o entorno aislado del cliente.

## Cuándo activar este modo

El `screenshot-capturer` recurre a este modo cuando:

1. No hay Playwright MCP, Chrome DevTools MCP ni Puppeteer MCP instalados.
2. Los CLIs (`playwright`, `chromium`, `wkhtmltoimage`) no están en el PATH.
3. La aplicación es móvil o de escritorio y el cliente no entrega un ambiente accesible.
4. El cliente prohíbe automatización por política de seguridad.

En este modo el plugin **no produce los PNGs**. Produce un documento detallado para que un humano (cliente o consultor en sitio) los tome y los entregue.

## Salida: `capturas/INSTRUCCIONES.md`

Una entrada por captura listada en `02-plan.md`:

```markdown
# Instrucciones para tomar las capturas manualmente

Total de capturas requeridas: N

Por favor, tome cada captura siguiendo las instrucciones de su bloque, guarde el archivo con el nombre exacto indicado y entregue la carpeta `capturas/` completa al equipo de documentación.

---

## Captura 1: `S03-pantalla-login.png`

**Sección del manual:** S03 — Acceso al sistema

**Resultado esperado:** captura de la pantalla de inicio de sesión, con los campos vacíos y sin mensajes de error.

**Pasos para tomarla:**

1. Abrir la aplicación en estado limpio (cerrar sesión si la había).
2. Navegar a `https://app.cliente.com/login`.
3. Verificar que la URL coincide y que la página muestra los textos del inventario:
   - Encabezado: "Bienvenido"
   - Botón principal: "Iniciar sesión"
4. **No** rellenar campos.
5. Capturar.

**Especificaciones técnicas:**

- Viewport / tamaño: 1366×768 (desktop) — usar zoom del navegador 100%.
- Idioma de la UI: español.
- Modo: claro.
- Formato: PNG.
- Tamaño máximo del archivo: 2 MB.

**Anotaciones requeridas:** ninguna.

**Riesgos a evitar:**

- No incluir información personal real en autocompletado de campos.
- Cerrar notificaciones de sistema antes de capturar.

---

## Captura 2: `S03-pantalla-login-error.png`

**Sección del manual:** S03 — Acceso al sistema

**Resultado esperado:** misma pantalla de login con mensaje de error de credenciales inválidas.

**Pasos para tomarla:**

1. Navegar a `https://app.cliente.com/login`.
2. Rellenar:
   - Correo electrónico: `demo@example.com`
   - Contraseña: `contrasena-incorrecta`
3. Hacer clic en "Iniciar sesión".
4. Esperar a que aparezca el mensaje: "Las credenciales no coinciden con nuestros registros."
5. Capturar.

**Especificaciones técnicas:**

- Viewport: 1366×768.
- Formato: PNG.

**Anotaciones requeridas:**

- Resaltar con un recuadro rojo el mensaje de error.

---

(... una entrada por cada captura del plan ...)
```

Cada bloque debe contener:

- **Nombre exacto del archivo** (idéntico al del plan).
- **Sección del manual** (ID + título).
- **Resultado esperado** (frase corta de qué muestra la captura).
- **Pasos para tomarla** (numerados, redactados como instrucciones operativas).
- **Especificaciones técnicas** (viewport, idioma, modo claro/oscuro, formato).
- **Anotaciones requeridas** (si las hay).
- **Riesgos a evitar** (datos sensibles, notificaciones, ventanas superpuestas).

## Comandos por SO para captura manual

Listar como referencia para el documento de instrucciones, según el SO del operador:

### Windows

| Acción | Atajo |
|--------|-------|
| Captura de pantalla completa | `PrtScr` (al portapapeles) |
| Captura de ventana activa | `Alt+PrtScr` |
| Captura recortada (Snipping Tool / Snip & Sketch) | `Win+Shift+S` |
| Captura completa al archivo | `Win+PrtScr` (carpeta Imágenes/Capturas) |

### macOS

| Acción | Atajo |
|--------|-------|
| Pantalla completa | `⌘+Shift+3` (archivo en Escritorio) |
| Selección rectangular | `⌘+Shift+4` |
| Ventana específica | `⌘+Shift+4` y luego `Espacio` |
| Captura con grabación | `⌘+Shift+5` |

### Linux (GNOME)

| Acción | Comando o atajo |
|--------|-----------------|
| Pantalla completa | `PrtScr` |
| Ventana | `Alt+PrtScr` |
| Selección | `Shift+PrtScr` |
| Herramienta CLI | `gnome-screenshot -a -f archivo.png` |

### Linux (KDE)

| Acción | Comando |
|--------|---------|
| Spectacle | `spectacle` (UI completa) |
| Selección rectangular | `spectacle -r -b -n -o archivo.png` |

### iOS

| Acción | Combinación |
|--------|-------------|
| Captura | `Botón lateral + Subir volumen` (Face ID) o `Inicio + Bloqueo` (Touch ID) |
| Captura larga (página completa) | Tras capturar, tocar "Página completa" en la previsualización |

### Android

| Acción | Combinación |
|--------|-------------|
| Captura | `Bloqueo + Bajar volumen` |
| Captura desplazable | Tras capturar, tocar "Captura ampliada" (depende del fabricante) |

## Editores recomendados para anotar

Sin imponer software:

| Plataforma | Opciones |
|------------|----------|
| Multi-plataforma | GIMP, Krita, Inkscape (vectorial sobre PNG), Skitch, Flameshot |
| Windows | Greenshot, ShareX, Snipping Tool, Paint.NET |
| macOS | Preview (anotaciones nativas), Skitch, Annotate |
| Linux | Flameshot (atajo a anotaciones tras captura), Shutter |

Sugerencias para mantener consistencia visual entre capturas:

- Color de resaltado uniforme (un único color para flechas y números, otro para tachado de datos sensibles).
- Grosor de línea consistente (3-4 px sobre capturas de 1366px).
- Tipografía de números: san-serif, blanco sobre círculo color, tamaño 24-28 px.

## Verificación tras la entrega manual

Cuando el cliente devuelve la carpeta `capturas/`, el `screenshot-capturer` debe:

1. Verificar que cada archivo del plan está presente con el nombre exacto.
2. Validar tamaño y dimensiones (rango razonable, formato PNG).
3. Listar archivos huérfanos (presentes pero no listados en el plan) y preguntar antes de mover.
4. Marcar el manifiesto con `herramienta: manual` y `estado: OK` para cada archivo verificado.
5. Reportar cualquier captura faltante o con dimensiones fuera de rango.
