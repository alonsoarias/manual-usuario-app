# Inspección de aplicaciones de escritorio

Guía operativa para que el `app-analyzer` recolecte datos en proyectos de escritorio. Las apps de escritorio añaden dimensiones que las webs y móviles no tienen: instaladores por SO, atajos de teclado, integración con el sistema de archivos y mecanismos de auto-actualización.

## Detección rápida del stack

| Archivo / patrón | Stack |
|------------------|-------|
| `package.json` con `electron`, `electron-builder` | Electron |
| `tauri.conf.json`, `Cargo.toml` con `tauri` | Tauri |
| `*.sln`, `*.csproj` con `WPF`, `WinForms`, `MAUI` | .NET (WPF / WinForms / MAUI) |
| `pom.xml` o `build.gradle` con `javafx`, `swing` | Java (JavaFX / Swing) |
| `*.pro`, `CMakeLists.txt` con `find_package(Qt`, `*.qml` | Qt (C++ o Python con PyQt/PySide) |
| `Info.plist` sin contexto iOS, target macOS | App nativa macOS (Swift/AppKit) |
| `*.iss`, `*.nsi` | Instaladores Inno Setup / NSIS |

## Electron

Búsquedas con grep:

```
grep -rn "BrowserWindow\|ipcMain\|ipcRenderer" src/
grep -rn "i18next\|electron-localization" .
cat package.json | grep -A 20 "build\|electron-builder"
```

Archivos clave:

- `package.json` con sección `build` (electron-builder) o `forge.config.{js,ts}`
- `src/main/`, `src/renderer/` — separación main/renderer
- `src/locales/`, `i18n/` — traducciones
- Configuración de auto-update: `electron-updater` o `autoUpdater` nativo

## Tauri

```
cat src-tauri/tauri.conf.json
ls src-tauri/src/
ls src/                                 # frontend (Vue/React/Svelte/Solid)
```

Archivos clave:

- `src-tauri/tauri.conf.json` — identidad de la app, permisos del backend, esquema de URL personalizado
- `src-tauri/src/main.rs` — comandos expuestos al frontend
- Frontend: stack web embebido (revisar `references/web-app.md` para la parte de UI)

## .NET (WPF / WinForms / MAUI)

```
find . -name "*.xaml"                   # WPF / MAUI
find . -name "*.Designer.cs"            # WinForms
grep -rn "ResourceDictionary\|StringResource" .
find . -name "*.resx"                   # recursos localizados
```

Archivos clave:

- WPF: `MainWindow.xaml`, `App.xaml`, `Resources/`
- WinForms: `*.cs` con clases que heredan de `Form`, `*.Designer.cs` autogenerados
- MAUI: `MainPage.xaml`, `App.xaml`, `Resources/Styles/`
- Localización: archivos `*.resx` por idioma (`Strings.resx`, `Strings.es.resx`)
- Configuración: `App.config`, `appsettings.json`

## Java (Swing / JavaFX)

```
find . -name "*.fxml"                   # JavaFX declarativo
find . -name "*.properties"             # bundles de internacionalización
grep -rn "ResourceBundle\.getBundle\|JFrame\|Stage" .
```

Archivos clave:

- JavaFX: `*.fxml`, controladores Java, `Main.java` con `extends Application`
- Swing: clases que heredan de `JFrame`, `JDialog`, `JPanel`
- Localización: `messages_{idioma}.properties` cargados con `ResourceBundle`
- Empaquetado: `pom.xml` con plugins `javafx-maven-plugin` o `jpackage`

## Qt (C++ o Python)

```
find . -name "*.qml"
find . -name "*.ui"
find . -name "*.ts" -path "*translations*"   # archivos de traducción Qt (.ts)
find . -name "*.qm"                         # binarios traducidos
```

Archivos clave:

- `*.qml` — vistas declarativas (Qt Quick)
- `*.ui` — vistas Qt Widgets (XML)
- `*.ts` (Qt Linguist) y `*.qm` compilados — traducciones
- `main.cpp` o `main.py` — punto de entrada
- `CMakeLists.txt` o `*.pro` — build

## Características transversales de escritorio

### Métodos de instalación

Inventariar **cada método** que el manual deba documentar.

| SO | Métodos típicos |
|----|-----------------|
| Windows | Instalador MSI, EXE (Inno Setup, NSIS), Microsoft Store, portable .zip, MSIX |
| macOS | DMG con drag-to-Applications, PKG, Mac App Store, Homebrew Cask |
| Linux | DEB (Debian/Ubuntu), RPM (RHEL/Fedora), AppImage, Flatpak, Snap, tarball .tar.gz |

Para cada método: dependencias previas, pasos de instalación, ubicación post-instalación, cómo desinstalar.

### Auto-actualización

Mecanismos típicos:

| Stack | Mecanismo |
|-------|-----------|
| Electron | `electron-updater` con feed Squirrel.Windows / Squirrel.Mac / generic |
| Tauri | Updater integrado, endpoint configurable en `tauri.conf.json` |
| .NET | ClickOnce, Squirrel, custom |
| Sparkle (macOS nativo) | Sparkle framework |
| WinSparkle (Windows nativo) | Equivalente para C/C++ |

Documentar la frecuencia de comprobación, si requiere intervención del usuario, dónde aparece la notificación de actualización disponible.

### Atajos de teclado

Recolectar todos los shortcuts globales y por pantalla. Diferenciar por SO (⌘ en macOS, Ctrl en Windows/Linux). Producir tabla apéndice.

| Acción | Windows | macOS | Linux |
|--------|---------|-------|-------|
| Nuevo documento | Ctrl+N | ⌘+N | Ctrl+N |

### Integración con el sistema de archivos

Inventariar:
- Asociaciones de archivos: extensiones que la app maneja.
- Esquemas de URL personalizados (`miapp://`).
- Carpetas estándar usadas: `~/Library/Application Support/...` (macOS), `%APPDATA%\...` (Windows), `~/.config/...` (Linux).
- Ubicación de logs y de la base local si existen.

### Iconos del bandeja del sistema (tray)

Si la app vive en la bandeja:
- Estado en cada situación (conectado, sincronizando, error).
- Menú contextual y opciones.
- Comportamiento al cerrar la ventana (¿se minimiza al tray o se cierra?).

### Modo offline / sincronización

Si aplica, describir:
- Qué funciones requieren conexión.
- Cómo detecta la app que está offline.
- Qué se cachea localmente y dónde.
- Cómo se sincronizan los cambios al recuperar la conexión.

## Tamaños de viewport para capturas

Recomendaciones por defecto:

| Tipo | Viewport |
|------|----------|
| Ventana principal estándar | 1366x768 |
| Ventana ancha (HD) | 1920x1080 |
| Diálogo modal | 600x400 (recortar a la ventana) |
| Captura del SO completa (raras) | resolución nativa |

## Reglas específicas de escritorio

### R1 — Una pasada por SO documentado

Si el brief incluye más de un SO, inspeccionar y capturar en cada uno. No extrapolar de uno a otro. Una pantalla en macOS no es la misma en Windows.

### R2 — Versión y arquitectura

Anotar versión y arquitectura (x86_64, ARM64) en `ambiente_inspeccion`. Algunas apps tienen builds distintas con UI sutilmente diferente.

### R3 — Permisos del SO

Documentar permisos que el SO solicita la primera vez (acceso a archivos, micrófono, cámara, accesibilidad en macOS, control total del disco, etc.).

### R4 — Estado limpio

Capturas iniciales con la app recién instalada. Si el manual cubre configuración, mostrar la pantalla "vacía" antes de la modificación y "configurada" después.
