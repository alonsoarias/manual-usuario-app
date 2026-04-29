# Plantillas por tipo de sección

Plantillas literales que el subagente del `manual-writer` debe seguir. Cada plantilla declara los encabezados obligatorios, los opcionales, y el orden. El review (criterio W5) verifica que la sección entregada respete la plantilla.

## Convenciones de la plantilla

- **`{placeholder}`** — texto a sustituir según contexto (brief, plan, inventario).
- **`# Título`** — encabezado obligatorio.
- **`## Subtítulo`** — encabezado obligatorio.
- **`### Subsubtítulo`** — encabezado opcional.
- **(opcional)** — bloque que puede omitirse si no aplica.

## 1. `portada`

```markdown
# {nombre_comercial}

## Manual de usuario

**Versión:** {version}
**Fecha:** {fecha_corte}
**Idioma:** {idioma}
**Audiencia:** {audiencia.perfil}

(opcional) Logo del cliente, datos de contacto, número de revisión.
```

Sin contenido de prosa. La portada es metadatos.

## 2. `tabla-contenido-auto`

Stub vacío con sólo frontmatter. Pandoc/Typst inyectan la tabla durante la compilación. El subagente no escribe contenido.

## 3. `introduccion`

```markdown
# Introducción

## Sobre este manual

(1-2 párrafos: qué cubre el manual, a quién está dirigido, qué versión documenta. Heredar del brief.)

## Audiencia y requisitos previos

(1 párrafo: perfil del lector y conocimientos asumidos. Si requiere conocimientos específicos, listarlos brevemente.)

## Convenciones tipográficas

A lo largo del manual se usan las siguientes convenciones:

- **Negrita** para nombres de botones y elementos accionables (p. ej. **Guardar**).
- *Cursiva* para nombres de campos de formulario (p. ej. *Correo electrónico*).
- `Monoespaciada` para valores literales, URL y código.
- "Comillas" para mensajes que muestra el sistema.

## Cómo usar este manual

(1 párrafo: si conviene leerlo en orden o saltar a la sección que interesa. Si hay índice, mencionarlo.)
```

## 4. `requisitos`

```markdown
# Requisitos previos

## Requisitos técnicos

| Requisito | Mínimo | Recomendado |
|-----------|--------|-------------|
| Sistema operativo | ... | ... |
| Navegador / app cliente | ... | ... |
| Conexión a internet | ... | ... |
| Otros | ... | ... |

## Cuenta y permisos

(1 párrafo: qué cuenta necesita y cómo obtenerla, si aplica.)

## Datos previos a tener a mano

- {dato 1}
- {dato 2}
```

## 5. `acceso`

```markdown
# Acceso al sistema

## Iniciar sesión

(1 párrafo introductorio.)

![Pantalla de inicio de sesión](capturas/{captura-login}.png)

1. Abra {URL o app}.
2. Escriba su correo en *Correo electrónico*.
3. Escriba su contraseña en *Contraseña*.
4. Pulse **Iniciar sesión**.

Tras un acceso correcto, el sistema lo dirige a {pantalla destino}.

**Si las credenciales no son correctas**, el sistema muestra el mensaje "{mensaje literal del inventario}". Verifique sus datos y vuelva a intentar.

## Recuperar la contraseña (opcional)

1. En la pantalla de inicio de sesión, pulse **¿Olvidó su contraseña?** (o el texto literal de la UI).
2. ...

## Cerrar sesión

1. ...
```

## 6. `modulo`

```markdown
# {Nombre del módulo}

## Para qué sirve

(1-2 párrafos: qué hace este módulo y cuándo se usa.)

## Cómo se accede

(1 párrafo o lista corta de pasos para llegar al módulo desde la pantalla principal.)

![Vista general del módulo](capturas/{captura-vista}.png)

## Elementos de la pantalla

(Sólo si la pantalla tiene una disposición compleja que conviene desglosar.)

| Elemento | Función |
|----------|---------|
| ... | ... |

## Tareas relacionadas

(Lista de tareas paso-a-paso que el lector puede ejecutar desde este módulo, con enlaces a sus secciones.)

- {Tarea 1} — sección "{título-tarea-1}"
- {Tarea 2} — sección "{título-tarea-2}"
```

## 7. `tarea-paso-a-paso`

```markdown
# {Título de la tarea, en infinitivo o gerundio según el brief}

## Cuándo realizarla

(1 párrafo: contexto. Cuándo el usuario necesita esta tarea.)

## Antes de empezar

(Lista de pre-requisitos. Si no hay, omitir.)

- ...

## Pasos

![{descripción de la captura inicial}](capturas/{captura-1}.png)

1. {Verbo en imperativo} {complemento}.
2. {Verbo en imperativo} {complemento}.

   ![{descripción}](capturas/{captura-2}.png)

3. {Verbo en imperativo} {complemento}.
4. Pulse **{botón}**.

## Resultado

(1 párrafo: qué cambia cuando termina con éxito. Mensaje del sistema literal si aplica.)

## Variantes y casos de error (opcional)

**Si {condición}**, el sistema {comportamiento}. Para resolverlo, {acción}.
```

## 8. `troubleshooting`

```markdown
# Solución de problemas

## {Síntoma 1: lo que el usuario observa}

**Causa probable:** {explicación corta y operativa}.

**Solución:**

1. ...
2. ...

## {Síntoma 2}

**Causa probable:** ...

**Solución:**

1. ...
```

Cada problema se nombra desde la perspectiva del usuario ("No puedo iniciar sesión"), no desde la perspectiva del sistema ("Error 401"). Si el sistema produce un código o mensaje específico, citarlo en la solución.

## 9. `glosario`

```markdown
# Glosario

**{Término 1}**
{Definición operativa, 1-3 frases. Sin redefinir términos del español general.}

**{Término 2}**
{Definición.}

...
```

Orden alfabético. Los términos provienen de la sección 5 del inventario. Sólo incluir términos específicos de la app o del dominio; no incluir vocabulario general.

## 10. `soporte`

```markdown
# Soporte y contacto

## Canales de ayuda

(Lista de canales con la información literal proporcionada por el cliente.)

- Correo: `{correo}`
- Teléfono: `{teléfono}`
- Portal de ayuda: `{URL}`
- Horario de atención: ...

## Antes de contactar al soporte

Para que la atención sea más eficaz, tenga a mano:

- Su {identificador de usuario / código de cliente}.
- La sección o pantalla en la que ocurre el problema.
- Una descripción de lo que esperaba que ocurriera.
- Una captura de pantalla del error, si aplica.

## Cómo reportar un incidente

1. ...
```

## 11. `apendice`

Plantilla genérica; el cuerpo varía según el contenido (atajos, tabla de roles, formatos de archivo, datos técnicos). Estructura mínima:

```markdown
# Apéndice {letra} — {tema}

## Propósito

(1 párrafo.)

## Contenido

(Tabla, lista o prosa según el tema.)
```

## 12. Reglas comunes a todas las plantillas

### R1 — Encabezados en orden

Los encabezados de la plantilla aparecen en el orden listado. No reordenar. Si una sección de la plantilla no aplica, omitirla **completa** (no dejar el título vacío).

### R2 — Una captura por bloque, no agrupar

Las capturas se intercalan con el texto que las explica. No producir un bloque con 5 capturas seguidas y luego un párrafo de texto.

### R3 — Pasos con verbo imperativo en negrita o sin formato (decidir y mantener)

Si el manual sigue convención "Pulse **Guardar**" (botón en negrita), aplicarla en todos los pasos. Si sigue "Pulse el botón Guardar" sin negrita, también — pero **una sola convención por manual**.

### R4 — Frase de resultado al final

Excepto en `portada`, `glosario`, `tabla-contenido-auto`, cada sección termina describiendo el resultado o el estado tras seguir las instrucciones. Confirma al lector que terminó.

### R5 — No crear plantillas nuevas

Si una sección no encaja en ninguna plantilla, revisar el plan: probablemente el tipo asignado es incorrecto o la sección no debería existir.
