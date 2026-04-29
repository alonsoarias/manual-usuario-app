// Plantilla Typst para el plugin manual-usuario-app.
// Se concatena al inicio del Typst convertido desde Markdown por Pandoc.
// Define configuración global de página, tipografía, encabezados, bloques de
// código, tablas, citas e imágenes. Sin marcas de cliente: estilo neutro.

#set page(
  paper: "a4",
  margin: (x: 2.5cm, y: 2.5cm),
  numbering: "1",
  number-align: center,
)

#set text(
  font: "DejaVu Sans",
  size: 11pt,
  lang: "es",
)

#set par(
  justify: true,
  leading: 0.65em,
  first-line-indent: 0em,
)

#set heading(numbering: "1.")

#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  set text(size: 22pt, weight: "bold")
  block(spacing: 1.2em)[#it]
}

#show heading.where(level: 2): it => {
  set text(size: 16pt, weight: "bold")
  block(above: 1.4em, below: 0.8em)[#it]
}

#show heading.where(level: 3): it => {
  set text(size: 13pt, weight: "bold")
  block(above: 1.0em, below: 0.5em)[#it]
}

#show raw.where(block: true): it => {
  block(
    fill: rgb("#f5f5f5"),
    inset: 10pt,
    radius: 4pt,
    width: 100%,
    text(font: "DejaVu Sans Mono", size: 9.5pt, it)
  )
}

#show raw.where(block: false): it => {
  box(
    fill: rgb("#f5f5f5"),
    inset: (x: 3pt, y: 1pt),
    outset: (y: 2pt),
    radius: 2pt,
    text(font: "DejaVu Sans Mono", size: 9.5pt, it)
  )
}

#show quote: it => block(
  fill: rgb("#fff8dc"),
  stroke: (left: 4pt + rgb("#ffaa00")),
  inset: (left: 12pt, top: 8pt, bottom: 8pt, right: 8pt),
  width: 100%,
  it
)

#show table: set table(
  stroke: 0.5pt + rgb("#888888"),
  inset: 6pt,
)

#show image: it => align(center, it)

#show link: it => underline(text(fill: rgb("#0050a0"), it))

#show outline.entry.where(level: 1): it => {
  set text(weight: "bold")
  it
}

#outline(title: [Tabla de contenido], depth: 3)

#pagebreak()
