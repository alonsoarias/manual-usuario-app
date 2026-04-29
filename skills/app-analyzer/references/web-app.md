# Inspección de aplicaciones web

Guía operativa para que el `app-analyzer` recolecte rutas, vistas, formularios, mensajes y traducciones en proyectos web populares. Cada bloque es independiente: aplicar sólo el del framework detectado en el repositorio.

## Detección rápida del framework

Pistas iniciales (regla 1: `Glob` y `Read` antes de asumir):

| Archivo / patrón | Framework probable |
|------------------|--------------------|
| `composer.json` con `"laravel/framework"` | Laravel |
| `composer.json` con `"symfony/framework-bundle"` | Symfony |
| `package.json` con `"next"` | Next.js |
| `package.json` con `"express"` | Express |
| `manage.py`, `settings.py`, `urls.py` | Django |
| `app.py` o `wsgi.py` con `Flask(...)` | Flask |
| `Startup.cs` o `Program.cs` con `WebApplication` | ASP.NET Core |
| `package.json` con `"react"` y sin backend | SPA React |
| `package.json` con `"vue"` y sin backend | SPA Vue |
| `angular.json` | SPA Angular |
| `nuxt.config.ts/js` | Nuxt |
| `astro.config.mjs` | Astro |

Si conviven varios (típico en monorepos), aplicar las pistas correspondientes a cada paquete.

## Laravel (PHP)

Comandos de descubrimiento (ejecutar en la raíz del repo si está disponible):

```
php artisan route:list --columns=method,uri,name,action,middleware
php artisan lang:list                 # solo Laravel 9+
```

Búsquedas con grep:

```
grep -rn "Route::" routes/
grep -rn "->validate(" app/Http/Controllers/
grep -rn "@error" resources/views/
grep -rn "trans(" resources/views/  resources/lang/
```

Archivos clave:

- `routes/web.php`, `routes/api.php` — rutas
- `app/Http/Controllers/` — endpoints
- `resources/views/` — Blade templates
- `resources/lang/{idioma}/` — strings traducidos
- `app/Http/Requests/` — validaciones
- `config/auth.php` — guards y proveedores

## Symfony (PHP)

```
bin/console debug:router
bin/console debug:translation {idioma}
bin/console debug:form
```

Archivos clave:

- `config/routes.yaml`, anotaciones `#[Route(...)]` en controladores
- `templates/` — Twig
- `translations/messages.{idioma}.yaml`
- `src/Form/` — clases de formulario

## Express (Node.js)

```
grep -rn "app\.\(get\|post\|put\|delete\|patch\)\|router\." routes/ src/
grep -rn "express-validator\|joi\|zod\|yup" .
```

Archivos clave:

- `app.js`, `server.js`, `routes/`, `controllers/`
- Validaciones: `express-validator`, `joi`, `zod`, `yup`
- Mensajes: típicamente inline; revisar `i18next` o `node-polyglot` si están

## Next.js

```
ls app/                               # App Router (Next 13+)
ls pages/                             # Pages Router (legado)
grep -rn "export default function" app/ pages/
```

Rutas: derivadas de la estructura de directorios.

- `app/[ruta]/page.tsx` o `pages/[ruta].tsx`
- `app/api/[ruta]/route.ts` para endpoints
- Localización: `next-intl`, `next-i18next`, archivos en `messages/{idioma}.json`

## Django (Python)

```
python manage.py show_urls            # requiere django-extensions
grep -rn "path(\|re_path(" */urls.py
grep -rn "_(" templates/ */views.py    # gettext
```

Archivos clave:

- `*/urls.py` — rutas
- `*/views.py` — endpoints
- `templates/` — templates
- `*/forms.py` — formularios y validaciones
- `locale/{idioma}/LC_MESSAGES/django.po` — traducciones gettext

## Flask (Python)

```
grep -rn "@app\.route\|@blueprint\.route" .
grep -rn "WTForms\|Form(" .
```

Archivos clave:

- `app.py` o módulos con `@app.route(...)`
- `templates/` — Jinja2
- `babel/translations/{idioma}/LC_MESSAGES/messages.po` si usa Flask-Babel

## ASP.NET Core (.NET)

```
grep -rn "MapGet\|MapPost\|MapControllerRoute" .
grep -rn "\[Route(\|\[Http" Controllers/
```

Archivos clave:

- `Program.cs`, `Startup.cs` — pipeline y rutas
- `Controllers/` — endpoints MVC
- `Pages/` — Razor Pages
- `Resources/` y `*.resx` — traducciones
- `appsettings.json` — configuración

## SPAs (React, Vue, Angular)

Sin servidor o con backend separado.

### React

```
grep -rn "createBrowserRouter\|<Route\|useRoutes" src/
grep -rn "react-i18next\|i18next" src/
```

Archivos clave: `src/router/`, `src/pages/`, `src/locales/{idioma}.json`

### Vue

```
grep -rn "createRouter\|VueRouter" src/
ls src/router/
ls src/locales/                       # vue-i18n típico
```

### Angular

```
grep -rn "RouterModule\|loadChildren\|path:" src/app/
ls src/assets/i18n/                    # ngx-translate típico
```

## Reglas comunes para todas las webs

### R1 — Idioma renderizado vs idioma del código

Las claves de traducción del código pueden no coincidir con lo que ve el usuario. Siempre verificar el archivo del idioma declarado en el brief (`resources/lang/es/...`, `messages/es.json`, etc.).

### R2 — Estados condicionales

Una pantalla puede mostrar mensajes distintos según rol o estado. Documentar ambos casos si el plan los pide. Marcarlos en la columna "Disparador" del inventario.

### R3 — Rutas dinámicas

`/courses/{id}` no es una ruta documentable: documentar el patrón. La captura debe usar un valor real anonimizado.

### R4 — Validaciones del lado servidor

Las validaciones declaradas en el código (FormRequest, FormType, validators) producen los mensajes del sistema cuando fallan. Inventariarlas.

### R5 — Modales y flujos asíncronos

Cuando una acción dispara un modal de confirmación, una notificación o un toast, registrarlo como una entrada separada en "Mensajes del sistema" con su disparador.
