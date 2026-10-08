# Inspección de SaaS multi-tenant y APIs

Guía operativa para que el `app-analyzer` inventaríe aplicaciones SaaS multi-tenant y APIs (REST, GraphQL, webhooks). La diferencia con `web-app.md`: aquí la unidad que cambia el comportamiento no es solo la ruta, es el **tenant** y el **plan** del tenant, y buena parte del inventario describe una API que no se navega con un navegador.

## Fuente del inventario: OpenAPI/Swagger primero

Antes de navegar a ciegas, buscar una especificación machine-readable. Cubre de un golpe rutas, parámetros, esquemas de request/response y a veces los roles/scopes exigidos por endpoint.

Pistas rápidas (regla 1 de `app-analyzer/SKILL.md`: `Glob`/`Grep`/`Read` antes de asumir):

```
curl -s https://{host}/api/docs
curl -s https://{host}/swagger.json
curl -s https://{host}/openapi.json
curl -s https://{host}/.well-known/openapi.json
grep -rln "openapi:\|swagger:" . 2>/dev/null
find . -iname "openapi.yaml" -o -iname "swagger.yaml" -o -iname "openapi.json"
```

Si existe la especificación:

- Cada `path` + `method` es una fila de «Módulos y rutas»; `operationId`/`summary` da el título.
- `security`/`securitySchemes` da los roles o scopes que acceden (columna «Roles que acceden»).
- `parameters` y `requestBody.schema` dan «Formularios y campos» — usar el `description` del esquema, no inventar etiquetas: si el esquema no trae label legible, lo que haya en la UI manda (regla de app-analyzer: texto literal, no parafraseado).
- Las respuestas `4xx`/`422` con `example` o `description` alimentan «Mensajes del sistema».
- Registrar la especificación misma como evidencia (`Evidencia: openapi.yaml#/paths/~1v1~1users`) en vez de archivo + línea cuando no hay archivo de código inspeccionable (nivel 2).

Si no existe especificación, caer al nivel de acceso disponible (código: `web-app.md` según el framework del backend; app desplegada: `screenshot-capturer` sobre el panel/consola).

## Planes y roles del tenant

Un SaaS casi siempre separa dos dimensiones que no deben mezclarse en una sola columna:

- **Rol** — qué puede hacer una persona dentro de un tenant (admin del tenant, miembro, solo-lectura). Va en «Roles y permisos» como siempre.
- **Plan** — qué funciones existen para ese tenant, independientemente de quién las use (free/starter/pro/enterprise). Añadir una tabla separada cuando el plan oculta o degrada una pantalla o una acción:

```markdown
## Planes y disponibilidad de funciones

| Función / pantalla | Free | Pro | Enterprise | Evidencia |
|---------------------|------|-----|------------|-----------|
| Exportar a CSV | no | sí | sí | `config/plans.php:40` |
| SSO (SAML) | no | no | sí | `billing/features.yaml:12` |
```

Si una pantalla del manual solo existe en ciertos planes, decirlo en la propia sección del manual (fase 5), no solo en el inventario: el lector con un plan inferior no debe seguir pasos que no puede ejecutar.

## Claves de API: siempre enmascaradas

Toda clave, token o secreto que aparezca en una pantalla (claves de API del tenant, tokens de webhook, secretos de firma) se enmascara con el mismo procedimiento y el mismo script que cualquier otro dato personal — no hay una regla aparte para SaaS. Fuente única: `skills/screenshot-capturer/references/pii-masking.md` (patrón `token`, sustituto `••••••••`). Esta referencia no duplica esa lógica: solo recuerda marcar `PII: sí` en «Módulos y rutas» para toda pantalla de gestión de claves de API, tokens o secretos de webhook, igual que cualquier otra pantalla con datos sensibles (regla R5 de `app-analyzer/SKILL.md`).

## Webhooks

Un webhook no es una pantalla que se capture: es una integración saliente. Inventariarlo en «Términos para glosario» o en una tabla propia si el plan dedica una sección a integraciones:

```markdown
## Webhooks

| Evento | Payload (campos clave) | Reintentos | Firma | Evidencia |
|--------|------------------------|------------|-------|-----------|
| `payment.succeeded` | `tenant_id`, `amount`, `currency` | 3, backoff exponencial | HMAC-SHA256 en cabecera `X-Signature` | `app/Webhooks/PaymentSucceeded.php:1` |
```

- Documentar el mecanismo de verificación de firma (si existe) como dato de seguridad del manual para desarrolladores integradores, nunca el secreto real usado para firmar.
- Si la UI tiene una pantalla de "registrar un webhook" o "ver entregas", esa pantalla sí se captura con `screenshot-capturer` y sigue la regla de PII normal (URLs de destino declaradas por el cliente pueden contener su propio dominio interno; no es dato personal por defecto, pero un payload de ejemplo con datos de un cliente real sí lo es).

## Reglas específicas SaaS/API

### R1 — Un tenant de demo, nunca el de un cliente real

Toda inspección y captura de un SaaS multi-tenant usa un tenant de prueba dedicado (ambiente de demo, regla ya exigida por `pii-masking.md`). Nunca se inspecciona ni se captura el tenant de un cliente real, aunque el inventario solo registre etiquetas.

### R2 — La especificación puede estar desincronizada del código

Si hay OpenAPI/Swagger **y** código, cruzar-verificar igual que en nivel 3 de `app-analyzer/SKILL.md`: la especificación puede no reflejar un endpoint nuevo o un campo renombrado. Reportar la divergencia en «Discrepancias detectadas».

### R3 — Rate limits y cuotas son parte del inventario, no del manual de desarrollador aparte

Si el plan free limita peticiones o recursos, documentarlo en la tabla de planes: es información que el usuario final necesita para entender un mensaje de error de cuota excedida.
