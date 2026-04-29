# Inspección de aplicaciones móviles

Guía operativa para que el `app-analyzer` recolecte datos en proyectos iOS, Android e híbridos. Las apps móviles añaden dimensiones que las webs no tienen: permisos del sistema, deep links, notificaciones push y modo sin conexión.

## Detección rápida del stack

| Archivo / patrón | Stack |
|------------------|-------|
| `*.xcodeproj`, `*.xcworkspace`, `Podfile` con `platform :ios` | iOS nativo (Swift/Objective-C) |
| `build.gradle(.kts)` con `com.android.application` | Android nativo (Kotlin/Java) |
| `ionic.config.json` o `capacitor.config.json/ts` | Ionic / Capacitor |
| `package.json` con `react-native` | React Native |
| `pubspec.yaml` | Flutter |
| `package.json` con `nativescript` | NativeScript |
| `tauri.conf.json` para móvil | Tauri Mobile |

## iOS (Swift)

Búsquedas con grep:

```
grep -rn "Localizable\.strings\|NSLocalizedString" .
grep -rn "Info\.plist" .
find . -name "*.storyboard" -o -name "*.xib"
find . -name "*.swift" | xargs grep -l "TextField\|Button\|Label"
```

Archivos clave:

- `*/{idioma}.lproj/Localizable.strings` — traducciones
- `Info.plist` — permisos solicitados (NSCameraUsageDescription, etc.) y esquemas de URL
- `*.storyboard` y `*.xib` — vistas declarativas
- `*.swift` con `@State`, `@Published` — vistas SwiftUI
- `Assets.xcassets/` — recursos visuales

## Android (Kotlin/Java)

```
find . -name "AndroidManifest.xml"
find . -path "*/values*/strings.xml"
find . -name "*.xml" -path "*/res/layout/*"
grep -rn "<intent-filter" .
```

Archivos clave:

- `app/src/main/AndroidManifest.xml` — permisos, activities, intent filters (deep links)
- `app/src/main/res/values{-idioma}/strings.xml` — strings y traducciones
- `app/src/main/res/layout/*.xml` — vistas declarativas
- `app/src/main/java/...` o `kotlin/...` — lógica
- Compose: archivos `.kt` con `@Composable`

Permisos comunes a inventariar:
`INTERNET`, `ACCESS_NETWORK_STATE`, `CAMERA`, `READ_EXTERNAL_STORAGE`, `WRITE_EXTERNAL_STORAGE`, `ACCESS_FINE_LOCATION`, `RECORD_AUDIO`, `POST_NOTIFICATIONS`.

## Ionic / Capacitor

```
cat capacitor.config.{json,ts}
ls src/app/                            # estructura Angular típica
grep -rn "Camera\|Geolocation\|Filesystem" src/
```

Archivos clave:

- `capacitor.config.{json,ts}` — id de la app, plugins, esquema
- `src/app/` — código (Angular, React o Vue según template)
- `android/app/src/main/AndroidManifest.xml` y `ios/App/App/Info.plist` para permisos

## React Native

```
cat package.json
grep -rn "navigation" src/
grep -rn "i18next\|i18n-js\|react-intl" .
```

Archivos clave:

- `App.{js,tsx}`, `src/`
- `android/app/src/main/AndroidManifest.xml`, `ios/{app}/Info.plist`
- `src/locales/` o `src/i18n/`
- Navegación: `react-navigation` (`Stack.Navigator`, `Tab.Navigator`)

## Flutter (Dart)

```
cat pubspec.yaml
grep -rn "MaterialApp\|CupertinoApp" lib/
grep -rn "AppLocalizations" lib/
ls lib/l10n/                           # archivos .arb
```

Archivos clave:

- `lib/main.dart` — punto de entrada
- `lib/screens/` o `lib/pages/` — pantallas
- `lib/l10n/{idioma}.arb` — traducciones
- `pubspec.yaml` — dependencias y assets
- `android/app/src/main/AndroidManifest.xml`, `ios/Runner/Info.plist`

## NativeScript

```
cat package.json
ls app/ src/
grep -rn "Page\|Frame" app/ src/
```

## Características transversales móviles

### Permisos del sistema

Inventariar **todos** los permisos solicitados, en qué pantalla se piden y con qué texto. iOS exige strings de propósito; Android usa runtime permissions desde API 23.

| Plataforma | Dónde mirar |
|------------|-------------|
| iOS | `Info.plist` claves `NS*UsageDescription` |
| Android | `AndroidManifest.xml` etiquetas `<uses-permission>` |

### Modo sin conexión

Inspeccionar:
- Cachés locales (Core Data, Room, Hive, Realm, SQLite, AsyncStorage).
- Lógica de sincronización (queues offline, retry policies).
- Mensajes que indican estado offline.

### Notificaciones

Diferenciar:
- **Push remotas** (FCM, APNs): registro de token, payload típico.
- **Locales** (NotificationManager, UNUserNotificationCenter): disparadores en el código.

Documentar la pantalla de configuración de notificaciones del sistema y de la app.

### Deep links / esquemas de URL

| Plataforma | Dónde mirar |
|------------|-------------|
| iOS | `Info.plist` clave `CFBundleURLTypes` (esquemas) y `applinks:` en `associated-domains` (Universal Links) |
| Android | `<intent-filter>` con `android:scheme` en `AndroidManifest.xml` |
| React Native | `Linking` API, configuración en archivos nativos |
| Flutter | Plugin `uni_links` o `app_links`, configuración en archivos nativos |

Inventariar cada esquema con el formato esperado y la pantalla a la que abre.

### Tamaños de viewport para capturas

Recomendaciones por defecto cuando el plan no especifique:

| Dispositivo | Viewport |
|-------------|----------|
| iPhone moderno | 390x844 |
| iPhone compacto | 375x812 |
| Android moderno | 412x915 |
| Android compacto | 360x800 |
| Tablet vertical | 768x1024 |
| Tablet horizontal | 1024x768 |

## Reglas específicas móviles

### R1 — Idioma del SO vs idioma de la app

La app puede heredar el idioma del SO o tener selector propio. Documentar el comportamiento y forzar el idioma del brief en las capturas.

### R2 — Onboarding no es opcional

La primera apertura típicamente muestra pantallas que no se repiten. Inventariarlas y planificar capturas en estado limpio (app desinstalada y reinstalada).

### R3 — Estado de red

Documentar comportamiento online y offline si la app declara soportar ambos. Las capturas en cada estado son diferentes.

### R4 — Versiones del SO

Las pantallas pueden variar entre versiones de iOS/Android. Anotar la versión del SO usada para las capturas en `ambiente_inspeccion`.
