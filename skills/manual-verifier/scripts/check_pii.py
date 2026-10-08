#!/usr/bin/env python3
"""Busca datos personales en un manual antes de entregarlo (mecanismo del check C13 de manual-verifier/SKILL.md).

Uso: check_pii.py DIRECTORIO_DEL_MANUAL

Revisa, desde la raíz del manual:
1. Texto: secciones/*.md y el texto de las salidas que existan en salida/ (manual.pdf vía pdftotext,
   manual.docx leyendo su XML —incluidos metadatos—, manual.html, manual.md). Patrones: correo, teléfono,
   documento de identidad, tarjeta (Luhn), IBAN (mod-97) y token/clave de API. Los mismos que enmascara
   screenshot-capturer/references/pii-masking.md (paridad probada en tests/test_pii_masking.py).
2. Capturas: cada pantalla con `PII: sí` en 03-inventario.md («Módulos y rutas») tiene `Enmascarado: sí` o
   `excepción: <motivo>` en capturas/MANIFIESTO.md, y todo PNG de capturas/ tiene su fila. Es una comprobación
   de convención, no OCR: lo que muestran los píxeles lo revisa a ojo el verificador (C13, paso visual).

No bloquean (lista documentada en manual-verifier/SKILL.md, C13): dominios reservados (example.com/.net/.org,
.example, .test, .invalid, .localhost), teléfonos ficticios (555-0100..0199 de NANP, 07700 900xxx y
020 7946 0xxx de Ofcom), tarjetas e IBAN de prueba conocidos, marcadores de relleno (menos de 4 caracteres
alfanuméricos distintos: 000 000 0000) y los valores de pii-permitidos.txt («valor | motivo», ambos obligatorios).

Imprime `ERROR: origen:línea: tipo (valor abreviado)` por hallazgo (línea donde empieza el párrafo), `PERMITIDO:` / `EXCEPCIÓN:` por cada
excepción usada (rastro auditable) y devuelve 0 (limpio), 1 (hallazgos) o 2 (uso incorrecto). El valor
completo nunca se reimprime: el informe de verificación no debe convertirse en otra copia del dato.
"""

from __future__ import annotations

import re
import subprocess
import sys
import unicodedata
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def digits(s: str) -> str:
    return re.sub(r"\D", "", s)


def luhn(d: str) -> bool:
    total = 0
    for i, c in enumerate(reversed(d)):
        n = int(c) * (2 if i % 2 else 1)
        total += n - 9 if n > 9 else n
    return total % 10 == 0


def iban_valid(s: str) -> bool:
    s = s.replace(" ", "")
    r = "".join(str(ord(c) - 55) if c.isalpha() else c for c in s[4:] + s[:4])
    return int(r) % 97 == 1


# En paridad con PATRONES de pii-masking.md: mismo orden, mismas expresiones, mismas validaciones.
# re.ASCII: \w y \b como en JavaScript.
PATTERNS = [
    ("token", r"\b(?:(?:sk|pk|rk)_(?:live|test)_[A-Za-z0-9]{10,}|sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|xox[abprs]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}|(?=[A-Za-z0-9_]*[A-Z])(?=[A-Za-z0-9_]*[a-z])(?=[A-Za-z0-9_]*\d)[A-Za-z0-9_]{32,})\b", 0, None),
    ("email", r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}", 0, None),
    ("iban", r"\b[A-Z]{2}\d{2}(?: ?[A-Z0-9]{4}){2,7}(?: ?[A-Z0-9]{1,4})?\b", 0, iban_valid),
    ("tarjeta", r"\b\d(?:[ -]?\d){12,18}\b", 0, lambda m: luhn(digits(m))),
    ("documento", r"\b(?:\d{3}\.\d{3}\.\d{3}-\d{2}|\d{3}-\d{2}-\d{4}|[XYZ]?\d{7,8}-?[A-Z])\b", 0, None),
    ("documento", r"\b(?:c\.? ?c\.?|c[ée]dula|documento|identificaci[oó]n|dni|nie|nit|cpf|rg|ssn|pasaporte|passport)(?![A-Za-z])[^\d\n]{0,15}\d[\d.\- ]{4,14}\d", re.I, None),
    ("telefono", r"(?<![\w.])(?:\+?\d{9,15}|(?:\+\d{1,3}[ -]?)?(?:\(\d{1,4}\)[ -]?)?\d{2,4}(?:[ -]\d{2,4}){1,4})(?![\w:/])", 0, lambda m: 9 <= len(digits(m)) <= 15),
]
PATTERNS = [(t, re.compile(p, f | re.ASCII), v) for t, p, f, v in PATTERNS]

RESERVED_DOMAINS = ("example.com", "example.net", "example.org")
RESERVED_TLDS = ("example", "test", "invalid", "localhost")
FICTITIOUS_PHONES = re.compile(r"(?:55501\d\d|^(?:44|0)?7700900\d{3}|^(?:44|0)?2079460\d{3})$")
TEST_CARDS = {"4111111111111111", "4242424242424242", "5555555555554444", "378282246310005"}
EXAMPLE_IBANS = {"GB82WEST12345698765432", "DE89370400440532013000"}


def compact(s: str) -> str:
    return re.sub(r"[\s().\-]", "", s).lower()


def fictitious(tipo: str, value: str) -> bool:
    if len({c for c in value.lower() if c.isalnum()}) < 4:
        return True
    if tipo == "email":
        domain = value.rsplit("@", 1)[1].lower()
        return domain in RESERVED_DOMAINS or domain.endswith(tuple("." + d for d in RESERVED_DOMAINS)) or domain.rsplit(".", 1)[-1] in RESERVED_TLDS
    if tipo == "telefono":
        return bool(FICTITIOUS_PHONES.search(digits(value)))
    if tipo == "tarjeta":
        return digits(value) in TEST_CARDS
    if tipo == "iban":
        return value.replace(" ", "") in EXAMPLE_IBANS
    return False


def find_pii(text: str) -> list[tuple[str, str]]:
    """(tipo, valor) por hallazgo, aplicando los patrones en orden y retirando lo ya encontrado."""
    hits: list[tuple[str, str]] = []
    for tipo, rx, valid in PATTERNS:
        def take(m: re.Match, tipo=tipo, valid=valid) -> str:
            if valid and not valid(m.group(0)):
                return m.group(0)
            hits.append((tipo, m.group(0)))
            return "\0"
        text = rx.sub(take, text)
    return hits


def abbreviate(value: str) -> str:
    return f"{value[:2]}…{value[-2:]}" if len(value) > 6 else "…"


class Problems:
    def __init__(self):
        self.errors: list[str] = []
        self.audit: list[str] = []


def load_permitted(root: Path, out: Problems) -> dict[str, str]:
    path = root / "pii-permitidos.txt"
    permitted: dict[str, str] = {}
    if not path.is_file():
        return permitted
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        value, _, reason = (p.strip() for p in line.partition("|"))
        if not value or not reason:
            out.errors.append(f"pii-permitidos.txt:{n}: cada línea es «valor | motivo»; falta el motivo o el valor")
            continue
        permitted[compact(value)] = reason
    return permitted


def scan_text(origin: str, text: str, permitted: dict[str, str], out: Problems):
    """Por párrafo (bloques separados por línea en blanco), con los saltos de línea como espacios: un dato que
    el autor o pandoc (72 columnas) partió entre dos líneas se sigue viendo. N = línea donde empieza el párrafo."""
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if line.strip() and (i == 0 or not lines[i - 1].strip())]
    for start in starts:
        end = next((j for j in range(start, len(lines)) if not lines[j].strip()), len(lines))
        n = start + 1
        for tipo, value in find_pii(" ".join(lines[start:end])):
            if fictitious(tipo, value):
                continue
            label = f"{origin}:{n}: {tipo} ({abbreviate(value)})"
            reason = permitted.get(compact(value))
            if reason:
                out.audit.append(f"PERMITIDO: {label} — {reason}")
            else:
                out.errors.append(label)


class HtmlText(HTMLParser):
    """Texto visible y atributos legibles (no src: las imágenes embebidas en base64 no son texto)."""

    ATTRS = {"alt", "title", "aria-label", "href", "content", "placeholder", "value"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.skip += 1
        self.parts += [v for k, v in attrs if k in self.ATTRS and v]

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def html_text(path: Path) -> str:
    """Un párrafo por nodo de texto o atributo: celdas vecinas de una tabla no se leen como un solo número."""
    parser = HtmlText()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    return "\n\n".join(parser.parts)


def docx_text(path: Path) -> str:
    """Párrafos de word/*.xml (uniendo los fragmentos w:t de cada w:p) y metadatos de docProps/."""
    lines: list[str] = []
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if not name.endswith(".xml") or not name.startswith(("word/", "docProps/")):
                continue
            tree = ElementTree.fromstring(z.read(name))
            paragraphs = list(tree.iter(W + "p"))
            if paragraphs:
                lines += ["".join(t.text or "" for t in p.iter(W + "t")) for p in paragraphs]
            else:
                lines += [t.strip() for t in tree.itertext() if t.strip()]
    return "\n\n".join(lines)


def pdf_text(path: Path) -> str:
    """Texto y metadatos. Sin poppler, subprocess lanza OSError y main lo cuenta como ERROR (nunca como pase)."""
    parts = []
    for cmd in (["pdftotext", str(path), "-"], ["pdfinfo", str(path)]):
        r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
        if r.returncode:
            raise RuntimeError(f"{cmd[0]} falló (rc {r.returncode}): {r.stderr.strip()[:200]}")
        parts.append(r.stdout)
    return "\n".join(parts)


OUTPUTS = {
    "manual.pdf": pdf_text,
    "manual.docx": docx_text,
    "manual.html": html_text,
    "manual.md": lambda p: p.read_text(encoding="utf-8", errors="replace"),
}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.strip().strip("`").strip())
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def table(path: Path, columns: set[str]) -> list[dict[str, str]] | None:
    """Filas (columna normalizada → celda) de la primera tabla Markdown que tiene todas `columns`."""
    rows: list[list[str]] = []
    header: list[str] | None = None
    for line in path.read_text(encoding="utf-8").splitlines() + [""]:
        if line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if header is None:
                header = [norm(c) for c in cells]
            elif not all(set(c) <= set("-: ") for c in cells):
                rows.append(cells)
            continue
        if header and columns <= set(header):
            return [dict(zip(header, r)) for r in rows]
        header, rows = None, []
    return None


def check_captures(root: Path, out: Problems):
    inventory = root / "03-inventario.md"
    manifest = root / "capturas" / "MANIFIESTO.md"
    for path in (inventory, manifest):
        if not path.is_file():
            out.errors.append(f"{path.relative_to(root)}: no existe; C13 no puede saber qué capturas muestran datos personales")
    if not (inventory.is_file() and manifest.is_file()):
        return
    screens = table(inventory, {"ruta / pantalla", "pii"})
    if screens is None:
        out.errors.append("03-inventario.md: «Módulos y rutas» no tiene las columnas «Ruta / Pantalla» y «PII» (esquema v2)")
        return
    pii: dict[str, bool] = {}
    for row in screens:
        screen, value = norm(row["ruta / pantalla"]), norm(row["pii"])
        if value not in {"si", "no"}:
            out.errors.append(f"03-inventario.md: la pantalla {row['ruta / pantalla']} tiene PII «{row['pii']}» (vale sí o no)")
            value = "si"  # a prueba de fallos
        pii[screen] = pii.get(screen, False) or value == "si"
    captures = table(manifest, {"archivo", "pantalla", "enmascarado"})
    if captures is None:
        out.errors.append("capturas/MANIFIESTO.md: le faltan las columnas «Pantalla» y «Enmascarado» (esquema v2)")
        return
    listed = set()
    for row in captures:
        name, screen, masked = row["archivo"].strip("` "), row["pantalla"], row["enmascarado"].strip()
        listed.add(name)
        if norm(screen) not in pii:
            out.errors.append(f"capturas/MANIFIESTO.md: {name}: la pantalla {screen} no está en 03-inventario.md")
            continue
        exception = re.match(r"(?i)excepci[oó]n\s*:\s*(.*)", masked)
        if exception:
            if not exception.group(1).strip():
                out.errors.append(f"capturas/MANIFIESTO.md: {name}: excepción sin motivo")
            else:
                out.audit.append(f"EXCEPCIÓN: {name} ({screen}) sin enmascarar — {exception.group(1).strip()}")
        elif norm(masked) not in {"si", "no"}:
            out.errors.append(f"capturas/MANIFIESTO.md: {name}: Enmascarado «{masked}» (vale sí, no o excepción: <motivo>)")
        elif pii[norm(screen)] and norm(masked) != "si":
            out.errors.append(f"capturas/MANIFIESTO.md: {name}: la pantalla {screen} tiene PII: sí en el inventario y no se enmascaró")
    for png in sorted((root / "capturas").glob("*.png")):
        if png.name not in listed:
            out.errors.append(f"capturas/{png.name}: sin fila en MANIFIESTO.md; no se puede afirmar que no muestra datos personales")


def main(argv: list[str]) -> int:
    if argv in (["-h"], ["--help"]):
        print(__doc__)
        return 0
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    root = Path(argv[0])
    if not (root / "secciones").is_dir():
        print(f"ERROR de uso: {root} no es la raíz de un manual (falta secciones/)", file=sys.stderr)
        return 2
    out = Problems()
    permitted = load_permitted(root, out)
    sources = sorted((root / "secciones").glob("*.md"))
    for path in sources:
        scan_text(f"secciones/{path.name}", path.read_text(encoding="utf-8", errors="replace"), permitted, out)
    for name, extract in OUTPUTS.items():
        path = root / "salida" / name
        if not path.is_file():
            continue
        sources.append(path)
        try:
            scan_text(f"salida/{name}", extract(path), permitted, out)
        except (RuntimeError, OSError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
            out.errors.append(f"salida/{name}: no se pudo extraer el texto ({exc})")
    check_captures(root, out)
    for line in out.audit:
        print(line)
    for line in out.errors:
        print(f"ERROR: {line}")
    print(f"{len(sources)} archivo(s) de texto comprobado(s): {', '.join(p.name for p in sources)}; {len(out.errors)} problema(s)")
    return 1 if out.errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
