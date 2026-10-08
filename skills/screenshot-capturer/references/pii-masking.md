# Datos personales en las capturas (fuente única)

Única fuente del enmascarado de datos personales (PII) del plugin. `playwright-mcp.md` y `chrome-devtools-mcp.md` enlazan aquí y no llevan copia propia. El check C13 de `manual-verifier` comprueba después lo que este procedimiento debía garantizar.

## Decisión: se sustituye el dato antes de capturar, nunca después

Un solo comportamiento: **ningún PNG con datos reales llega a `capturas/`.** El dato se sustituye en la pantalla (DOM) antes de pulsar el obturador; no se captura y se tacha después.

Motivo:

1. Un PNG con datos reales ya es una copia del dato fuera del sistema del cliente. `capturas/` se comparte, se embebe en el DOCX/PDF/HTML y se entrega a terceros; una vez publicado no se puede retirar. Tachar después deja una ventana en que el original existe, y depende de acertar los píxeles.
2. En el DOM el texto es exacto: se sabe qué cadena es un correo y dónde está. Sobre un PNG habría que reconocer el texto (OCR), y el entorno no tiene `tesseract`.
3. La sustitución conserva la maqueta (mismo tipo de dato, longitud parecida), así que la captura sigue sirviendo para el paso que ilustra.

Orden de preferencia:

1. **Ambiente de demo con datos sintéticos** (lo pide `screenshot-capturer/SKILL.md`, «Estado de la app»). Aun así se ejecuta el script: no cuesta nada y cubre el dato real que se haya colado.
2. **Sustitución en el DOM con el script de abajo**, antes de cada captura de una pantalla marcada para enmascarar.
3. **Sin DOM** (app móvil o de escritorio, fallback manual, CLI): la captura se hace con una cuenta de demo. Si es imposible, el original se guarda **fuera del directorio del manual** (directorio temporal), se tapan los datos con rectángulos opacos `#37474f` con Pillow (no con el naranja `#ff5722` de las anotaciones, que cuenta en C11), se mueve a `capturas/` solo la versión tapada y se borra el original.

## Cuándo se enmascara

Lo decide el dato, no el criterio del capturador en el momento:

| Plan (`enmascarar`) | Inventario (`pii`) | Se enmascara | Manifiesto (`Enmascarado`) |
|---|---|---|---|
| `sí` | cualquiera | sí | `sí` |
| `no` | `no` | no (el script puede correr igual) | `no` |
| `no` | `sí` | **sí**: el inventario manda, a prueba de fallos | `sí` |
| `excepción: <motivo>` | `sí` | no | `excepción: <motivo>` |

- La única forma de no enmascarar una pantalla con `pii: sí` es una excepción explícita con motivo, aprobada por el PO en el plan (p. ej. «ambiente de demo con datos sintéticos verificados por el cliente»). C13 la acepta, la imprime como `EXCEPCIÓN:` en el informe y la incluye en la revisión visual.
- El capturador no decide no enmascarar. Puede enmascarar de más (lo inofensivo), nunca de menos.

## Script de detección y enmascarado

Se pasa tal cual como la función de `browser_evaluate` (Playwright MCP) o de `evaluate_script` (Chrome DevTools MCP). Devuelve `{ enmascarado: { email: N, telefono: N, ... } }`: anota esa cuenta en el manifiesto o en el log de la fase.

Por captura, editar solo las tres constantes del principio con lo que diga el inventario (nombres de personas visibles, selectores de nombre y de foto de la app concreta).

<!-- pii-mask:script -->
```js
() => {
  // Nombres reales visibles en la pantalla (inventario, cabecera "Bienvenido, ..."): se sustituyen donde aparezcan.
  const NOMBRES_REALES = [];
  // Elementos cuyo texto entero es el nombre de una persona.
  const SELECTORES_PERSONA = '[data-user-name], .user-name, .username, .userpicture + .username, '
    + 'select[name*="user"] option:not([value=""]), select[name*="usuario"] option:not([value=""])';
  // Fotos de personas: <img> y fondos CSS.
  const SELECTORES_AVATAR = 'img[class*="avatar"], .avatar img, img[class*="profile"], img[class*="perfil"], '
    + 'img[alt*="foto" i], img[alt*="photo" i], img[src*="gravatar"]';
  const SELECTORES_FONDO_AVATAR = '[class*="avatar"], [class*="profile-photo"], [class*="foto-perfil"]';

  const SILUETA = 'data:image/svg+xml,' + encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><rect width="40" height="40" fill="#cfd8dc"/>'
    + '<circle cx="20" cy="15" r="8" fill="#90a4ae"/><rect x="6" y="27" width="28" height="13" rx="6" fill="#90a4ae"/></svg>');
  const digitos = (s) => s.replace(/\D/g, '');
  const luhn = (d) => {
    let suma = 0;
    for (let i = 0; i < d.length; i++) {
      let n = Number(d[d.length - 1 - i]);
      if (i % 2) { n *= 2; if (n > 9) n -= 9; }
      suma += n;
    }
    return suma % 10 === 0;
  };
  const ibanValido = (s) => {
    const r = (s.slice(4) + s.slice(0, 4)).replace(/[A-Z]/g, (c) => String(c.charCodeAt(0) - 55));
    let resto = 0;
    for (const c of r) resto = (resto * 10 + Number(c)) % 97;
    return resto === 1;
  };

  // El orden es la prioridad: lo que un patrón ya sustituyó no lo reinterpreta el siguiente.
  // Cada regex /g se usa solo con String.replace (que reinicia lastIndex); nunca con .test(), que lo arrastra
  // entre llamadas sobre el mismo objeto y da true/false alternos.
  // Mantener en paridad con PATTERNS de manual-verifier/scripts/check_pii.py (lo prueba tests/test_pii_masking.py).
  const PATRONES = [
    ['token', /\b(?:(?:sk|pk|rk)_(?:live|test)_[A-Za-z0-9]{10,}|sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|xox[abprs]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}|(?=[A-Za-z0-9_]*[A-Z])(?=[A-Za-z0-9_]*[a-z])(?=[A-Za-z0-9_]*\d)[A-Za-z0-9_]{32,})\b/g,
      () => '••••••••'],
    ['email', /[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}/g, () => 'usuario@example.com'],
    ['iban', /\b[A-Z]{2}\d{2}(?: ?[A-Z0-9]{4}){2,7}(?: ?[A-Z0-9]{1,4})?\b/g,
      (m) => (ibanValido(m.replace(/ /g, '')) ? 'XX** **** **** ****' : m)],
    ['tarjeta', /\b\d(?:[ -]?\d){12,18}\b/g, (m) => (luhn(digitos(m)) ? '**** **** **** ****' : m)],
    ['documento', /\b(?:\d{3}\.\d{3}\.\d{3}-\d{2}|\d{3}-\d{2}-\d{4}|[XYZ]?\d{7,8}-?[A-Z])\b/g, (m) => m.replace(/\d/g, '*')],
    ['documento', /\b(?:c\.? ?c\.?|c[ée]dula|documento|identificaci[oó]n|dni|nie|nit|cpf|rg|ssn|pasaporte|passport)(?![A-Za-z])[^\d\n]{0,15}\d[\d.\- ]{4,14}\d/gi,
      (m) => m.replace(/\d/g, '*')],
    ['telefono', /(?<![\w.])(?:\+?\d{9,15}|(?:\+\d{1,3}[ -]?)?(?:\(\d{1,4}\)[ -]?)?\d{2,4}(?:[ -]\d{2,4}){1,4})(?![\w:/])/g,
      (m) => (digitos(m).length >= 9 && digitos(m).length <= 15 ? '555-0100' : m)],
  ];

  const cuenta = {};
  const anotar = (tipo) => { cuenta[tipo] = (cuenta[tipo] || 0) + 1; };
  const enmascarar = (texto) => {
    // Un salto de línea del HTML se pinta como espacio: sin esto, «cédula\n1.023.456.789» no se reconoce.
    // Si nada se enmascara se devuelve el texto original (con sus saltos, que en <pre>/<textarea> se ven).
    let t = texto.replace(/\n/g, ' ');
    let cambiado = false;
    for (const [tipo, re, sustituto] of PATRONES) {
      t = t.replace(re, (m) => {
        const r = sustituto(m);
        if (r !== m) { anotar(tipo); cambiado = true; }
        return r;
      });
    }
    for (const nombre of NOMBRES_REALES) {
      if (nombre && t.includes(nombre)) { t = t.split(nombre).join('Usuario Demo'); anotar('nombre'); cambiado = true; }
    }
    return cambiado ? t : texto;
  };

  document.querySelectorAll(SELECTORES_PERSONA).forEach((el, i) => { el.textContent = `Usuario Demo ${i + 1}`; anotar('nombre'); });

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
  document.querySelectorAll('[title], [alt], [aria-label], [placeholder], [href^="mailto:"], [href^="tel:"]').forEach((el) => {
    for (const a of ['title', 'alt', 'aria-label', 'placeholder', 'href']) {
      const v = el.getAttribute(a);
      if (!v) continue;
      const m = enmascarar(v);
      if (m !== v) el.setAttribute(a, m);
    }
  });

  document.querySelectorAll(SELECTORES_AVATAR).forEach((img) => {
    img.closest('picture')?.querySelectorAll('source').forEach((s) => s.remove());
    img.removeAttribute('srcset');
    img.src = SILUETA;
    img.alt = 'Usuario Demo';
    anotar('avatar');
  });
  document.querySelectorAll(SELECTORES_FONDO_AVATAR).forEach((el) => {
    if (getComputedStyle(el).backgroundImage !== 'none') { el.style.backgroundImage = `url("${SILUETA}")`; anotar('avatar'); }
  });

  // ponytail: no entra en iframes ni shadow DOM; si la pantalla los usa, ejecutar el script dentro de cada uno.
  return { enmascarado: cuenta };
}
```

Qué cubre y qué no:

| Dato | Cómo | Sustituto |
|---|---|---|
| Correo | patrón | `usuario@example.com` |
| Teléfono (9-15 dígitos, con `+`, paréntesis, espacios o guiones) | patrón | `555-0100` |
| Documento: CPF, SSN, DNI/NIE con letra, y cualquier número tras «cédula / C.C. / documento / DNI / NIT / CPF / pasaporte...» | patrón | dígitos → `*` |
| Tarjeta (13-19 dígitos que pasan Luhn) | patrón + Luhn | `**** **** **** ****` |
| IBAN (dígito de control mod-97 válido) | patrón + mod-97 | `XX** **** **** ****` |
| Token / clave de API (`sk_live_`, `ghp_`, `AKIA`, `AIza`, `xox?-`, JWT, o 32+ caracteres que mezclan mayúscula, minúscula y dígito) | patrón | `••••••••` |
| Nombre de persona | `SELECTORES_PERSONA` + `NOMBRES_REALES` | `Usuario Demo N` |
| Foto de persona | `SELECTORES_AVATAR`, `SELECTORES_FONDO_AVATAR` | silueta gris |

- **Nombres:** no hay patrón fiable para un nombre propio. Se cubren por selector y por la lista de nombres que el capturador lee de la pantalla (cabecera, `browser_snapshot`) antes de capturar. Lo que se escape lo caza la revisión visual de C13.
- **Datos partidos** entre nodos (`ana@<b>cliente</b>.co`), dentro de un `<canvas>` o en una imagen: el script no los ve. Revisar la captura antes de guardarla.
- **Teléfonos con puntos** (`300.123.4567`) no se detectan: los puntos separan versiones e IP, que no deben enmascararse.
- Tras capturar, si la sesión sigue en uso, recargar la página para volver al estado real.

## Procedimiento con Playwright MCP

1. Navegar y llevar la pantalla al estado del plan (ver `playwright-mcp.md`, «Patrón recomendado por captura»).
2. `browser_snapshot` para leer los nombres de personas visibles y rellenar `NOMBRES_REALES`.
3. `browser_evaluate` con el script.
4. Aplicar las anotaciones del plan (recuadro, numeración...): la anotación y el enmascarado son independientes y conviven en la misma captura.
5. `browser_snapshot` otra vez y buscar en el texto que no quede ningún dato real; si queda, ampliar los selectores y repetir el paso 3.
6. `browser_take_screenshot`.
7. Manifiesto: `Enmascarado: sí` (o `excepción: <motivo>` si el plan lo declaró así).

## Procedimiento con Chrome DevTools MCP

La sesión es la real del usuario: aquí el riesgo es mayor (cuenta propia, datos de producción, extensiones con el nombre del usuario).

1. `list_pages` / `select_page` sobre la pestaña con la pantalla en el estado del plan.
2. Leer los nombres de personas visibles (`evaluate_script` con `document.body.innerText`) y rellenar `NOMBRES_REALES`.
3. `evaluate_script` con el mismo script.
4. Aplicar las anotaciones del plan.
5. Comprobar con `evaluate_script` (`document.body.innerText`) que no quede ningún dato real.
6. `take_screenshot`.
7. Manifiesto como en Playwright. Al terminar, recargar la pestaña: el usuario sigue trabajando en ella.

`take_screenshot` de Chrome DevTools captura solo el área de la página: el nombre de la cuenta en la barra de perfil de Chrome no sale. Si se usa una captura del SO (con la barra del navegador), recortar esa zona o taparla según el punto 3 de «Decisión».
