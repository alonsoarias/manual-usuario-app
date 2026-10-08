# Delta por idioma (es / en / pt)

Este archivo NO repite `tone-and-voice.md` ni `section-templates.md`: esas dos
son la base del redactor, escrita en y para español, y se siguen aplicando
tal cual (voz activa, frases cortas, un verbo por paso, vocabulario a evitar
por marketing-speak, patrones de captura+texto, etc.) sea cual sea el idioma
del manual. Aquí sólo vive lo que CAMBIA al redactar en `en` o `pt`, más la
tabla de es para que el redactor no tenga que saltar entre dos documentos
para la misma decisión.

El `idioma` lo fija `01-brief.md` (es, en, pt; admite región: `pt-BR`, `en`).
Es el mismo campo que usa `concatenate.py` (tabla `LANGUAGES`,
`skills/manual-compiler/SKILL.md`) para el subtítulo y el título de la TOC;
este archivo cubre el resto de la prosa que el compilador no toca.

## Tratamiento al lector

Mismo criterio de `tone-and-voice.md` §1.3 (lo decide el brief; por defecto
el registro formal del idioma): se traduce el EJE tú/usted a su equivalente
formal/informal en cada idioma, nunca se mezcla dentro del mismo manual.

| Idioma | Formal (equivalente a "usted") | Informal (equivalente a "tú") |
|---|---|---|
| es | usted — "Haga clic", "su cuenta" | tú — "Haz clic", "tu cuenta" |
| en | you (el inglés no distingue registro por pronombre) — "Click", "your account"; el registro formal se marca con cortesía ("Please click...") y vocabulario, no con el pronombre | you — igual, sin "please"; imperativo directo |
| pt | o/a senhor(a) + 3ª persona — "Clique", "a sua conta" | você + imperativo — "Clica", "a tua/sua conta" (pt-BR prefiere "você" también en informal; pt-PT usa "tu") |

Nota para `en`: como el pronombre no cambia, la variable de registro es
"please"/cortesía y evitar contracciones en formal ("do not" vs "don't").
Mantener la elección en todo el manual, igual que en es.

## Etiquetas fijas

Estas tres etiquetas aparecen literal en el cuerpo del manual (notas,
advertencias, numeración de pasos) y deben traducirse siempre igual, nunca
parafrasearse, para que un lector que compare manuales en varios idiomas
reconozca la misma convención:

| Español | English | Português |
|---|---|---|
| Paso | Step | Passo |
| Nota | Note | Nota |
| Advertencia | Warning | Aviso |

Uso: igual que en es (`tone-and-voice.md` §2.2 — "Nota", "Importante" con
moderación, sólo cuando la información es crítica). "Advertencia"/"Warning"/
"Aviso" se reserva para riesgo de pérdida de datos o de tiempo; "Nota"/
"Note"/"Nota" para una aclaración que no es crítica.

## Vocabulario a evitar (delta por idioma)

Los adjetivos vacíos y verbos confusos de `tone-and-voice.md` §3.1-3.2 son
universales (traducir el concepto, no la palabra española literal: "amigable"
→ evitar igual "user-friendly"/"amigável"). Lo que SÍ cambia por idioma es la
lista de anglicismos/falsos cercanos a evitar:

### en

| Evitar | Usar |
|---|---|
| Utilize | Use |
| In order to | To |
| Please note that | (omitir; ir directo a la nota) |
| Kindly | (omitir) |
| Click on the button | Click the button (sin "on" en instrucciones de UI) |

### pt

| Evitar | Usar |
|---|---|
| Clicar (calco de "clic" + verbo genérico sin objeto) | Clique em **Salvar** |
| Deletar | Excluir |
| Printar | Imprimir |
| Resetar | Redefinir, reiniciar |
| Logar / Logar-se | Fazer login, iniciar sessão |
| Settar | Configurar |

## Cómo lo usa el redactor

Cada subagente de `manual-writer` recibe, además de `tone-and-voice.md` y
`section-templates.md` (siempre, sea cual sea el idioma): este archivo
(`languages.md`), filtrado a la fila/sección del `idioma` del brief. Si el
idioma es `es`, `languages.md` no aporta nada nuevo frente a
`tone-and-voice.md` (son las mismas reglas) y basta con confirmar el
tratamiento; si es `en` o `pt`, el tratamiento y el vocabulario a evitar de
este archivo sustituyen a los ejemplos en español de `tone-and-voice.md`
cuando entren en conflicto (p. ej. la tabla de anglicismos §3.3 de
`tone-and-voice.md` no aplica a un manual en `en`).
