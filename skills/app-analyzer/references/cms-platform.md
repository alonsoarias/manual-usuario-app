# Inspección de plataformas CMS

Guía operativa para que el `app-analyzer` recolecte datos en plataformas tipo Moodle, OJS, WordPress, Drupal y Joomla. Las CMS añaden una dimensión clave: el **núcleo** y los **plugins/extensiones** activados producen una UI distinta en cada instalación.

## Detección rápida

| Archivo / patrón | Plataforma |
|------------------|------------|
| `version.php` con `$plugin->component = 'core'` y `mod/`, `blocks/` | Moodle |
| `lib.classes.php` con `OJS_VERSION` o `config.inc.php` con `installed = On` | OJS (Open Journal Systems) |
| `wp-config.php` o tabla `wp_options` | WordPress |
| `core/` con `core.services.yml` y `composer.json` `drupal/core` | Drupal |
| `configuration.php` con `class JConfig` | Joomla |

Las cinco plataformas tienen en común: **núcleo + extensiones modifican la UI**. La inspección debe partir de listar las extensiones activas antes de inventariar pantallas.

## Moodle

### Listado de plugins activos

Si hay shell access:

```
mysql -u {user} -p {db} -e "SELECT plugin, name, value FROM mdl_config_plugins WHERE name='version' ORDER BY plugin;"
```

O por filesystem:

```
find . -maxdepth 3 -name "version.php" -exec grep -l "plugin->component" {} \;
```

Ubicaciones típicas de plugins:

| Tipo | Carpeta |
|------|---------|
| Actividades / módulos | `mod/{plugin}/` |
| Bloques | `blocks/{plugin}/` |
| Formatos de curso | `course/format/{plugin}/` |
| Temas | `theme/{plugin}/` |
| Filtros | `filter/{plugin}/` |
| Reportes | `report/{plugin}/` |
| Métodos de matriculación | `enrol/{plugin}/` |
| Métodos de pago | `paygw/{plugin}/` |

### Strings y traducciones

```
find . -path "*/lang/{idioma}/*.php"
grep -rn "get_string(" --include="*.php"
```

Archivos clave:

- `lang/{idioma}/{plugin}.php` — strings por plugin e idioma
- `customlang/` — traducciones personalizadas del cliente (¡crítico, sobreescriben el core!)

### Roles y permisos

```
mysql ... -e "SELECT shortname, name FROM mdl_role;"
mysql ... -e "SELECT roleid, capability, permission FROM mdl_role_capabilities WHERE permission != 0;"
```

O vía UI: `/admin/roles/manage.php` (capturar para evidencia).

### Configuración por sitio

Variables que cambian la UI: `$CFG->theme`, `$CFG->forcelogin`, capacidad por defecto, plugins habilitados. Inventariar valores actuales del sitio.

## OJS / Open Journal Systems

### Estructura

OJS funciona por **revistas dentro de una instalación**. Cada revista puede tener su propia configuración, plugins y traducciones. Antes de inspeccionar, identificar **qué revista** documenta el manual.

```
ls plugins/                            # plugins instalados
cat config.inc.php | grep -E "locale|installed"
```

Roles típicos a documentar (cada uno con UI diferente):

- Lector
- Autor
- Revisor
- Editor de sección
- Editor jefe
- Gestor de revista
- Administrador del sitio

Cada flujo editorial es distinto: envío, revisión, edición, copyediting, layout, publicación. Inventariar por etapa y por rol.

### Strings

```
find locale/{idioma}/ -name "*.po" -o -name "*.xml"
grep -rn "__(\|translate(" --include="*.tpl"
```

## WordPress

### Listado de plugins y temas activos

```
mysql -u {user} -p {db} -e "SELECT option_value FROM wp_options WHERE option_name='active_plugins';"
mysql ... -e "SELECT option_value FROM wp_options WHERE option_name='template';"
mysql ... -e "SELECT option_value FROM wp_options WHERE option_name='stylesheet';"
```

Por filesystem:

- `wp-content/plugins/` — todos los plugins (la lista de activos sale de la base)
- `wp-content/themes/{tema}/` — tema activo
- `wp-content/mu-plugins/` — must-use plugins (siempre activos)

### Strings y traducciones

```
find . -name "*.po" -o -name "*.mo"
grep -rn "__(\|_e(\|esc_html__(" --include="*.php"
```

Archivos: `wp-content/languages/{plugin-o-theme}-{idioma}.po`

### Tipos de contenido y campos personalizados

WordPress permite custom post types y custom fields que cambian completamente las pantallas de edición.

```
grep -rn "register_post_type\|register_taxonomy" wp-content/
grep -rn "ACF\|advanced-custom-fields" wp-content/
```

Si el sitio usa Advanced Custom Fields, Toolset, Pods u otro framework, inventariar los grupos de campos que el usuario verá.

## Drupal

### Listado de módulos activos

```
drush pm:list --status=enabled --type=module
```

O por base:

```
mysql ... -e "SELECT name, type, status FROM key_value WHERE collection='system.schema';"
```

Carpetas:

- `core/modules/` — módulos del core
- `modules/` o `modules/contrib/` — contribuidos
- `modules/custom/` — desarrollados a medida del cliente
- `themes/` — temas

### Strings

```
drush locale:check                     # estado de traducciones
find . -name "*.po"
```

### Tipos de contenido y vistas

Drupal define la mayoría de la UI vía **content types**, **fields**, **views** y **paragraphs**. Exportar la configuración:

```
drush config:export --destination=/tmp/drupal-config
```

Archivos clave en la exportación:

- `node.type.{tipo}.yml`
- `field.field.node.{tipo}.{campo}.yml`
- `views.view.{vista}.yml`

## Joomla

### Listado de extensiones

```
mysql ... -e "SELECT name, type, element, enabled FROM #__extensions WHERE enabled=1;"
```

Tipos: `component`, `module`, `plugin`, `template`, `language`.

### Strings

Archivos `*.ini` por idioma:

```
find . -path "*/language/{idioma}/*.ini"
```

Cada extensión tiene su propio bundle de strings.

## Reglas comunes para CMS

### R1 — Plugins primero, pantallas después

No inspeccionar pantallas sin saber qué plugins están activos. La misma pantalla de edición de curso en Moodle puede tener 5 o 50 campos según los plugins instalados.

### R2 — Traducciones personalizadas del cliente

Las CMS permiten sobreescribir strings del core. Inspeccionar siempre las customizaciones antes de inventariar el texto del core. Si una cadena no aparece donde el código del plugin la declara, buscar en customlang/translation override del cliente.

### R3 — Núcleo vs personalizaciones

Distinguir en el inventario qué pantallas vienen del core de la plataforma y cuáles son customizaciones del cliente. Esto importa para futuras actualizaciones.

### R4 — Roles y permisos como cuadrante

Producir una matriz "Pantallas × Roles" indicando qué rol ve cada pantalla. Es habitual que una sección del manual aplique sólo a un rol.

### R5 — Multi-instancia (multi-sitio, multi-revista)

Si la instalación aloja varios sitios o revistas, especificar **cuál** se documenta. Las pantallas de configuración global vs por sitio cambian.

### R6 — Versiones del core y de plugins

Anotar en `ambiente_inspeccion` las versiones exactas del core y de los plugins activos. Una actualización menor puede mover botones de lugar.
