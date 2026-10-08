# Inspección de flujos de autenticación

Guía operativa para que el `app-analyzer` inventaríe login, SSO (OIDC/SAML), verificación en dos pasos (2FA/TOTP) y recuperación de cuenta. Estos flujos cruzan cualquier tipo de app (`web-app.md`, `mobile-app.md`, `desktop-app.md`, `cms-platform.md`, `saas-api.md`) y comparten un riesgo que ninguno de esos documentos cubre: varios de sus pasos producen un secreto de un solo uso, y un código o enlace de recuperación real capturado en un PNG ya es una fuga, exista o no PII en el sentido de `pii-masking.md`.

## Login simple

Sin dimensión adicional: documentar como cualquier formulario (`web-app.md`/`mobile-app.md` según el stack). Campos, validaciones, mensajes de credenciales inválidas, bloqueo tras N intentos si existe.

## SSO (OIDC/SAML)

El flujo típico sale de la app del cliente y entra al Identity Provider (IdP): Google, Microsoft Entra ID, Okta, un IdP SAML propio.

**Regla dura: nunca capturar pantallas del IdP de terceros sin permiso explícito del cliente.** La pantalla de login de Google/Microsoft/Okta no es propiedad de la app documentada; capturarla:

- Puede mostrar el correo o el nombre de una cuenta real del cliente o del capturador.
- Puede violar los términos de uso del IdP o la política de marca (logos, layout) del tercero.
- Documenta una UI que el cliente no controla y que puede cambiar sin aviso, volviendo el manual obsoleto.

Antes de capturar cualquier paso de SSO: confirmar con el PO/cliente si está autorizado. Si no hay autorización o no se puede confirmar, documentar el flujo con texto («se abre la pantalla de inicio de sesión de su proveedor de identidad corporativo») y una captura solo del punto exacto donde la app propia retoma el control (pantalla post-redirección), nunca de la pantalla del IdP.

Qué inventariar igualmente (sin captura del IdP):

- Qué IdPs soporta la app (botones «Iniciar sesión con Google/Microsoft/SAML») — captura del selector, que sí es UI propia.
- El mensaje de error que la app propia muestra si el SSO falla o el usuario no está provisionado.
- Si hay aprovisionamiento automático (JIT) de usuarios vs invitación manual.

## 2FA / TOTP

Un código de 2FA (TOTP de 6 dígitos, código SMS, enlace de aprobación push) es un secreto de un solo uso, y el QR y la clave de enrolamiento son la semilla que genera todos los códigos futuros de la cuenta. **Ningún secreto de autenticación real llega a una captura ni a la herramienta del agente.** Es la misma decisión que `pii-masking.md` («Decisión: se sustituye el dato antes de capturar, nunca después»): el secreto se sustituye en la pantalla (DOM) antes de pulsar el obturador; no se captura y se tacha después.

El script de `pii-masking.md` no basta aquí: sus patrones no reconocen un código de 6 dígitos, una semilla Base32 ni un código de respaldo (no tienen prefijo de clave de API ni mezclan mayúsculas, minúsculas y dígitos). El script de abajo los localiza primero por selector y después, como red de respaldo, recorre todo el texto, los campos y los atributos visibles con sus propios patrones (semilla Base32, código de respaldo, código de 6 dígitos), igual que el recorrido de `pii-masking.md`.

Cómo llevar el flujo a la captura:

1. Usar una **cuenta de prueba dedicada** (nunca la cuenta personal del capturador ni una de un cliente real), con 2FA habilitado solo en esa cuenta.
2. Pantalla que **pide** el código (campo vacío, «Introduce el código de 6 dígitos de tu app de autenticación»): no contiene secretos; se captura con el procedimiento normal de `pii-masking.md`.
3. Pantalla con el código **ya introducido** («así se ve el código completado»): no se genera ningún código. Se ejecuta el script de abajo, que escribe el valor de ejemplo `000000` en el campo, y solo entonces se captura. En el texto del manual, si hace falta mostrar el formato, se usa ese mismo valor de ejemplo (`000000` o `123456`), nunca uno generado por la cuenta de prueba.
4. Pasar el 2FA de verdad para capturar las pantallas posteriores: el código real lo escribe la persona a mano en la ventana del navegador, no el agente con `browser_type`/`fill` (dejaría el código en el registro de la sesión), y no se captura nada hasta que cargue la pantalla siguiente, que ya no lo muestra.
5. Enrolamiento (QR, clave para introducir a mano, códigos de respaldo): se ejecuta el script de abajo **antes** de cualquier `browser_snapshot` o lectura de `document.body.innerText`, porque esas lecturas copian la clave en claro al registro de la sesión; después, el procedimiento normal de `pii-masking.md` y la captura. El script sustituye el QR (lo marcado por selector, todo `<canvas>` y toda imagen o `<svg>` casi cuadrado de 96 px o más) por un recuadro gris y cada letra o dígito de la clave y de los códigos por `0`.
6. **Comprobar antes de capturar**, con el resultado del propio script (no leyendo `document.body.innerText` ni con `browser_snapshot`: si quedara un secreto, esa lectura lo copiaría al registro de la sesión). `sin_revisar.residuo` cuenta lo que, en el texto y los campos que la captura vería, aún tiene forma de código, clave Base32 o código de respaldo, por ejemplo un secreto partido entre etiquetas; `sin_revisar.iframe` y `sin_revisar.shadow` cuentan las zonas donde el script no entra. Si alguno es mayor que 0: ampliar `SELECTORES_CLAVE` / `SELECTORES_QR` (o ejecutar el script dentro del iframe) y repetir hasta que los tres valgan 0. Un QR que el script no reconoce (ni por selector, ni por ser `<canvas>`, ni por tamaño) no lo detecta ninguna comprobación: se añade su selector a `SELECTORES_QR` **antes** de capturar, mirando la pantalla, nunca tapándolo después en el PNG.
   **`residuo: 0` no es «ya no queda ningún secreto»: usa los mismos patrones que el enmascarado, así que comparte sus puntos ciegos.** No detecta una clave Base32 en minúsculas (el patrón solo reconoce mayúsculas, por evitar falsos positivos con palabras comunes de 4 letras) ni un código de respaldo con espacio en vez de guión (`a1b2 c3d4`). Tampoco detecta un secreto partido por una etiqueta de bloque (`<br>`, `<div>`, `<p>`); solo lo detecta si el corte es dentro de una etiqueta en línea (`<span>`, `<b>`). Ante cualquiera de esos formatos, revisar la captura a ojo antes de guardarla, sin confiar solo en `residuo`.
7. Sin DOM (app móvil o de escritorio): la pantalla de enrolamiento y la de código completado no se capturan; se describen con texto. El punto 3 de «Orden de preferencia» de `pii-masking.md` (guardar el original fuera del manual y taparlo) no vale para una semilla de 2FA: ese original ya sería la semilla en claro en disco.

Por captura, editar solo las constantes del principio con los selectores de la app concreta (inventario). Enmascarar de más es inofensivo.

<!-- auth-secret:script -->
```js
() => {
  // Campos donde se escribe el código (uno solo, o una casilla por dígito).
  const SELECTORES_CODIGO = 'input[autocomplete="one-time-code"], input[name*="otp" i], input[name*="code" i], input[name*="codigo" i], input[name*="totp" i]';
  // Elementos cuyo texto es una clave de enrolamiento o un código de respaldo.
  const SELECTORES_CLAVE = '[class*="secret" i], [class*="recovery-code" i], [class*="backup-code" i], [class*="codigo-respaldo" i], [data-secret]';
  // El QR de enrolamiento: <img>, <canvas> o <svg>, suelto o dentro de un contenedor "qr".
  const SELECTORES_QR = 'img[class*="qr" i], img[alt*="qr" i], img[src^="otpauth" i], canvas[class*="qr" i], svg[class*="qr" i], '
    + '[class*="qr" i] img, [class*="qr" i] canvas, [class*="qr" i] svg';
  const CODIGO_EJEMPLO = '000000';

  const RECUADRO = 'data:image/svg+xml,' + encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><rect width="40" height="40" fill="#cfd8dc"/></svg>');
  const ceros = (m) => m.replace(/[A-Za-z0-9]/g, '0');

  // Red de respaldo para lo que ningún selector marcó; misma estructura que PATRONES de pii-masking.md.
  // El sustituto devuelve m intacto si no es un secreto (así no se cuenta como enmascarado ni como residuo).
  const PATRONES = [
    // Semilla Base32 (RFC 4648, mayúsculas): seguida o en grupos de 4 separados por espacio.
    ['clave', /\b(?:[A-Z2-7]{16,}|[A-Z2-7]{4}(?: [A-Z2-7]{4}){3,})\b/g, ceros],
    // Código de respaldo: xxxx-xxxx / xxxxx-xxxxx con algún dígito («self-host» no lo es), o 8 dígitos en dos grupos.
    ['respaldo', /\b(?:[A-Za-z0-9]{4,5}-[A-Za-z0-9]{4,5}|\d{4} \d{4})\b/g, (m) => (/\d/.test(m) ? ceros(m) : m)],
    // Código de un solo uso: 6 dígitos aislados, seguidos o en dos grupos de 3.
    ['codigo', /(?<![\w.,])(?:\d{6}|\d{3} \d{3})(?![\w.,])/g, ceros],
  ];

  const cuenta = {};
  const anotar = (tipo) => { cuenta[tipo] = (cuenta[tipo] || 0) + 1; };
  const enmascarar = (texto) => {
    let t = texto;
    for (const [tipo, re, sustituto] of PATRONES) {
      t = t.replace(re, (m) => { const r = sustituto(m); if (r !== m) anotar(tipo); return r; });
    }
    return t;
  };

  document.querySelectorAll(SELECTORES_CODIGO).forEach((el) => {
    const v = el.maxLength === 1 ? '0' : CODIGO_EJEMPLO;
    el.value = v; el.setAttribute('value', v); anotar('codigo');
  });
  document.querySelectorAll(SELECTORES_CLAVE).forEach((el) => { el.textContent = ceros(el.textContent); anotar('clave'); });

  // QR: lo marcado por selector, todo <canvas> (en una pantalla de 2FA no hay otro uso que valga la pena conservar)
  // y toda imagen o <svg> casi cuadrado de 96 px o más (los iconos son menores). Enmascarar de más es inofensivo.
  const cuadradoGrande = (el) => {
    const r = el.getBoundingClientRect();
    return Math.min(r.width, r.height) >= 96 && Math.abs(r.width - r.height) <= 0.1 * r.width;
  };
  const qrs = new Set([...document.querySelectorAll(SELECTORES_QR), ...document.querySelectorAll('canvas'),
    ...[...document.querySelectorAll('img, svg')].filter(cuadradoGrande)]);
  qrs.forEach((el) => {
    if (!el.isConnected) return; // ya cayó con un ancestro sustituido
    const r = el.getBoundingClientRect();
    const img = document.createElement('img');
    img.src = RECUADRO; img.alt = 'Código QR de ejemplo';
    img.width = Math.round(r.width) || 160; img.height = Math.round(r.height) || 160;
    el.replaceWith(img); anotar('qr');
  });
  document.querySelectorAll('[href^="otpauth:" i]').forEach((el) => { el.setAttribute('href', '#'); anotar('enlace'); });

  // Respaldo sobre todo el texto, los campos y los atributos visibles (mismos tres recorridos que pii-masking.md).
  const recorrido = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
    acceptNode: (n) => (['SCRIPT', 'STYLE', 'NOSCRIPT'].includes(n.parentNode.nodeName) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT),
  });
  for (let n = recorrido.nextNode(); n; n = recorrido.nextNode()) {
    const v = enmascarar(n.nodeValue);
    if (v !== n.nodeValue) n.nodeValue = v;
  }
  document.querySelectorAll('input, textarea').forEach((el) => {
    const v = enmascarar(el.value);
    if (v !== el.value) { el.value = v; el.setAttribute('value', v); }
  });
  document.querySelectorAll('[title], [alt], [aria-label], [placeholder]').forEach((el) => {
    for (const a of ['title', 'alt', 'aria-label', 'placeholder']) {
      const v = el.getAttribute(a);
      if (v && enmascarar(v) !== v) el.setAttribute(a, enmascarar(v));
    }
  });

  // Comprobación (paso 6): lo que aún parece un secreto en lo que la captura vería. Solo cuentas, nunca el texto:
  // devolverlo copiaría el secreto al registro de la sesión. Un secreto partido entre nodos (<b>, <span>) escapa al
  // recorrido por nodo pero aparece entero en innerText.
  const visible = [document.body.innerText, ...[...document.querySelectorAll('input, textarea')].map((e) => e.value)].join('\n');
  let residuo = 0;
  for (const [, re, sustituto] of PATRONES) visible.replace(re, (m) => { if (sustituto(m) !== m) residuo++; return m; });
  const iframe = document.querySelectorAll('iframe').length;
  const shadow = [...document.querySelectorAll('*')].filter((e) => e.shadowRoot).length;

  // ponytail: no entra en iframes ni shadow DOM (igual que pii-masking.md): los cuenta en sin_revisar para que se ejecute dentro.
  return { enmascarado: cuenta, sin_revisar: { residuo, iframe, shadow } };
}
```

## Recuperación de cuenta

El enlace o código de "olvidé mi contraseña" es también de un solo uso y expira. Las mismas reglas que 2FA:

- **Nunca capturar un enlace o código de recuperación real.** Un enlace de recuperación es equivalente a una contraseña temporal: quien lo vea puede tomar la cuenta.
- Capturar el formulario que **pide** el correo/usuario (sin secretos) y el mensaje de confirmación genérico ("Si el correo existe, enviamos un enlace") — ninguno de los dos expone nada.
- Para la pantalla de "nueva contraseña": la persona abre a mano, en la ventana del navegador, el enlace real que recibió la cuenta de prueba (el agente no lo lee del correo ni lo pasa a `browser_navigate`: quedaría en el registro de la sesión). La pantalla suele seguir llevando el token en su propia URL (`/reset/<token>` o `?token=`), así que se captura **solo el área de la página** (`browser_take_screenshot` de Playwright, `take_screenshot` de Chrome DevTools), que no incluye la barra de direcciones, y con el procedimiento normal de `pii-masking.md` antes del obturador. Después, completar el cambio de contraseña para que el enlace quede invalidado por el uso.
- Captura del SO o sin DOM (la barra de direcciones o el enlace saldrían en el PNG): la pantalla no se captura; se describe con texto. Recortar o tapar después no vale: el original con el token ya existiría en disco.

## Reglas específicas de autenticación

### R1 — Cuenta de prueba dedicada, siempre

Todo flujo de esta referencia (SSO, 2FA, recuperación) se inspecciona y captura con una cuenta de prueba creada para el manual, nunca con una cuenta personal o de un cliente real. Es el mismo principio que `pii-masking.md` exige para el resto de capturas, aplicado a credenciales en vez de a datos de perfil.

### R2 — Un secreto capturado se trata como comprometido

Si por error un código, token o enlace real queda en una captura, no basta con tacharlo después: el secreto ya existió en claro en un archivo. Se invalida/revoca ese secreto (cambiar la contraseña, forzar la expiración del código, rotar la clave de API) además de descartar o enmascarar el PNG. Reportarlo como discrepancia/incidente, no silenciarlo.

### R3 — El IdP de terceros no se documenta en profundidad sin más que el permiso cubra

El permiso del cliente para capturar su propio IdP (si lo tiene self-hosted) no se extiende automáticamente a documentar la UI de un IdP que el cliente no controla (Google, Microsoft, Okta como servicio). Ante la duda, texto descriptivo sin captura.
