# Tono y voz para manuales de usuario

Reglas de redacción que cada subagente del `manual-writer` debe seguir y que el review (criterios W7 y W8) verifica.

## 1. Reglas de oro

### 1.1 Voz activa

| Evitar (pasiva) | Usar (activa) |
|-----------------|----------------|
| El botón es presionado por el usuario | Pulse el botón |
| Los datos serán guardados al confirmar | El sistema guarda los datos al confirmar |
| Se debe completar el formulario | Complete el formulario |
| El correo será enviado | El sistema envía el correo |

### 1.2 Tiempo presente

| Evitar | Usar |
|--------|------|
| Cuando haya pulsado el botón, aparecerá la confirmación | Al pulsar el botón, aparece la confirmación |
| Esto le permitirá editar el contenido | Esto le permite editar el contenido |
| Se mostrará la lista | Aparece la lista |

### 1.3 Segunda persona

Tratamiento al lector según declaración del cliente. Si el brief no lo declara, usar `usted`. Mantener la decisión en **todo el manual**.

| Tratamiento | Cuándo |
|-------------|--------|
| Usted | Manuales corporativos, sector salud, sector público, audiencia heterogénea, idioma neutro |
| Tú | Productos consumer, audiencia joven, productos lifestyle, redes |

Si el cliente prefiere impersonal ("se hace clic"), respetarlo aunque conviva con voz activa: "haga clic" pasa a ser "hacer clic" en infinitivo. Esta decisión va en el brief.

### 1.4 Un verbo por paso

Cada paso describe **una sola acción** del usuario.

| Evitar | Usar |
|--------|------|
| Pulse Guardar y espere a que aparezca la confirmación | 1. Pulse **Guardar**. 2. Espere la confirmación. |
| Inicie sesión y luego entre al panel | 1. Inicie sesión. 2. Abra el panel principal. |

### 1.5 Frases cortas

| Nivel TIC | Máximo de palabras por frase |
|-----------|------------------------------|
| Bajo | 15 |
| Medio | 25 |
| Alto | 35 |

Las cifras son límites superiores, no targets. Frases más cortas siempre son aceptables.

### 1.6 Tipografía consistente

| Elemento | Convención |
|----------|------------|
| Botones | **Negrita**: pulse **Guardar** |
| Campos de formulario | *Cursiva*: complete el campo *Correo electrónico* |
| Valores literales (URL, comandos, código) | `Monoespaciada`: navegue a `https://app.cliente.com/login` |
| Mensajes del sistema | "Comillas" o citas en bloque |
| Nombres de pantallas | **Negrita** o sin formato (decidir y mantener) |
| Nombres de roles, módulos | Sin formato, con mayúscula inicial sólo si lo requiere el inventario |

Estas convenciones se declaran en la sección "Convenciones tipográficas" del manual (típicamente en la introducción) y se aplican uniformemente.

## 2. Patrones por tipo de instrucción

### 2.1 Camino feliz (paso a paso)

```
1. Abra **Mi cuenta**.
2. Pulse **Editar perfil**.
3. Complete los campos *Nombre* y *Correo electrónico*.
4. Pulse **Guardar**.

Aparece el mensaje "Cambios guardados". El sistema actualiza su perfil.
```

### 2.2 Variante o caso de error

```
**Si las credenciales no son correctas**, el sistema muestra el mensaje "Las credenciales no coinciden con nuestros registros." Verifique que su correo y contraseña están bien escritos y vuelva a intentar.
```

Recurrir a `**Nota**`, `**Importante**` o cajas resaltadas con moderación, sólo cuando la información es crítica para no perder datos o tiempo.

### 2.3 Referencia a otra sección

```
Para detalles sobre cómo recuperar la contraseña, consulte la sección **Recuperación de contraseña**.
```

Evitar referencias por número ("véase la sección 4.2"): la numeración cambia con renumeraciones.

### 2.4 Captura como apoyo

```
La pantalla de inicio de sesión presenta dos campos y un botón.

![Pantalla de inicio de sesión](capturas/S03-pantalla-login.png)

1. Escriba su correo en *Correo electrónico*.
2. Escriba su contraseña en *Contraseña*.
3. Pulse **Iniciar sesión**.
```

La captura aparece **después** del párrafo introductorio y **antes** de la lista de pasos.

## 3. Vocabulario a evitar

### 3.1 Adjetivos vacíos (bloqueante en review W8)

| Evitar | Por qué |
|--------|---------|
| intuitivo | No describe nada concreto |
| fácil de usar | Subjetivo |
| amigable | Cliché |
| moderno | Datado en cuanto se publica |
| robusto | Marketing speak |
| potente | Marketing speak |
| eficiente | Salvo dato medible |
| innovador | Marketing speak |
| rápido | Salvo cifra concreta |
| sencillo | Subjetivo |

### 3.2 Verbos confusos

| Evitar | Usar |
|--------|------|
| Hacer | Verbo concreto: pulsar, escribir, seleccionar, marcar, abrir |
| Realizar | Verbo concreto |
| Efectuar | Verbo concreto |
| Llevar a cabo | Verbo concreto |
| Proceder a | (omitir, ir directo al verbo) |

### 3.3 Anglicismos innecesarios

Cuando exista equivalente común y el manual está en español:

| Evitar | Usar |
|--------|------|
| Loguearse, logearse | Iniciar sesión |
| Postear | Publicar |
| Linkar | Enlazar |
| Customizar | Personalizar |
| Setear | Configurar |
| Resetear | Restablecer, reiniciar |
| Submitir | Enviar |
| Deletear | Eliminar, borrar |

Excepción: cuando la propia UI use el anglicismo, citarlo literal y explicarlo la primera vez.

### 3.4 Tecnicismos sin explicar

Si una sección debe usar un término técnico, definirlo la primera vez en el cuerpo o remitir al glosario:

> El **token** es una clave temporal que el sistema genera para verificar su identidad.

Después de la primera mención, usar el término sin redefinir.

## 4. Tiempos verbales

| Acción | Tiempo |
|--------|--------|
| Instrucción al usuario | Imperativo: "Pulse", "Escriba", "Seleccione" |
| Resultado del sistema | Presente: "Aparece la confirmación", "El sistema envía un correo" |
| Pre-requisito | Presente: "El sistema requiere…" |
| Caso condicional | Presente subjuntivo o indicativo: "Si introduce un correo no registrado, …" |
| Descripción de pantalla | Presente: "La pantalla muestra…" |

Evitar futuro y condicional salvo para futuros ciertos posteriores a una acción.

## 5. Tratamiento al lector — `tú` vs `usted`

Una vez decidido en el brief, se mantiene en todo el manual. La mezcla es la marca más visible de inconsistencia. Verificar especialmente:

- Imperativos: "Haz clic" vs "Haga clic".
- Posesivos: "tu cuenta" vs "su cuenta".
- Pronombres: "te aparece" vs "le aparece".

## 6. Integración de capturas con texto

Patrón recomendado:

1. **Frase introductoria** (opcional, 1 frase): qué muestra la captura, no más.
2. **Captura**.
3. **Pasos** numerados que la usan.

Anti-patrón: capturas sin contexto. Cada captura debe tener al menos una mención en el texto que la rodea.

## 7. Referencias cruzadas

- A otras secciones: por **título**, no por número.
- A capturas: por nombre de archivo o cuerpo del párrafo, nunca por figura/tabla numerada (Pandoc maneja numeración automática si se decide en compile).
- A elementos de UI: por nombre literal del inventario.

## 8. Listas

| Caso | Lista |
|------|-------|
| Pasos secuenciales | Numerada |
| Opciones independientes | Con viñetas |
| Variantes de un mismo paso | Con viñetas dentro del paso |
| Conjuntos pequeños | Texto en línea con comas si caben en 1-2 frases |

Mantener paralelismo gramatical: si el primer item empieza con verbo en imperativo, todos los siguientes también.

## 9. Errores comunes a vigilar

- "Click here" → "Aquí" no es link; nombrar el destino: "Pulse **Iniciar sesión**".
- "Por favor, haga clic…": redundancia. Decir directamente "Haga clic…".
- "Como se puede ver en la imagen…": redundante; la imagen ya se ve.
- "Es muy importante que…" / "Es necesario…": cargados, suelen ser pasos imperativos sin marca: "Confirme el envío para…".
- Mezcla de dos verbos en el mismo paso: dividir.
- Capturas con datos personales reales: bloqueante; reemplazar.
- Listas de un solo elemento: pasar a párrafo.
