#!/usr/bin/env python3
"""Comprueba que una salida web del manual (HTML autocontenido o Markdown GFM) es portable y no filtra rutas.

Uso: check_web_output.py ARCHIVO.html|ARCHIVO.md|DIRECTORIO [...]

Un directorio comprueba sus .html y .md (sin recursión). Imprime una línea `ERROR: archivo: motivo` por
problema (stdout) y devuelve 0 si no hay ninguno, 1 si los hay, 2 por uso incorrecto (stderr).

Comprueba, en cada archivo:
- ningún `file:` ni ruta de usuario (/home/, /Users/, /root/, C:\\Users\\, el HOME de quien ejecuta);
- cada imagen/recurso resuelve: `data:` o un archivo relativo que existe junto al archivo (no remoto, no absoluto);
- ningún contenido activo: <script>, <iframe>, <object>, <embed>, atributos on*=, enlaces `javascript:`.

Script standalone: hoy no lo invoca ningún SKILL.md ni comando automáticamente. Pensado para que una
fase posterior del verificador lo enganche a un check propio sobre `salida/manual.html` y `salida/manual.md`.
"""

from __future__ import annotations

import re
import sys
import urllib.parse
from html.parser import HTMLParser
from pathlib import Path

USER_PATH_RE = re.compile(r"(?:/home/|/Users/|/root/|[A-Za-z]:\\Users\\)[^\s\"'<>)]*")
FILE_URL_RE = re.compile(r"file:/", re.IGNORECASE)
ABSOLUTE_RE = re.compile(r"^(?:/|[A-Za-z]:[\\/]|\\)")
REMOTE_RE = re.compile(r"^(?:[a-zA-Z][a-zA-Z0-9+.-]*:|//)")
CSS_URL_RE = re.compile(r"url\(\s*(['\"]?)([^'\")\s]+)\1\s*\)", re.IGNORECASE)
MD_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)")
ACTIVE_TAGS = {"script", "iframe", "object", "embed"}
RESOURCE_ATTRS = {"src", "poster", "data"}  # <a href> no es un recurso: sólo se vigila que no sea local
SAFE_SCHEMES = ("mailto:", "tel:")


def classify(value: str, base: Path, resource: bool) -> str | None:
    """Motivo por el que `value` no es portable, o None."""
    value = value.strip()
    if not value or value.startswith(("#", "data:")) or value.lower().startswith(SAFE_SCHEMES):
        return None
    if FILE_URL_RE.match(value):
        return f"URL file: ({value})"
    if ABSOLUTE_RE.match(value) and not value.startswith("//"):
        return f"ruta absoluta local ({value})"
    if REMOTE_RE.match(value):
        return f"recurso remoto, no autocontenido ({value})" if resource else None
    if resource:
        target = urllib.parse.unquote(re.split(r"[?#]", value)[0])
        resolved = (base / target).resolve()
        if base.resolve() not in resolved.parents:
            return f"el recurso queda fuera del directorio de la salida ({value})"
        if not resolved.is_file():
            return f"el recurso no resuelve junto al archivo ({value})"
    return None


class Usage(Exception):
    """Argumento inválido (rc 2)."""


class Scanner(HTMLParser):
    def __init__(self, base: Path):
        super().__init__(convert_charrefs=True)
        self.base = base
        self.problems: list[str] = []
        self.in_style = False

    def handle_endtag(self, tag):
        self.in_style = self.in_style and tag != "style"

    def handle_starttag(self, tag, attrs):
        self.in_style = tag == "style"
        if tag in ACTIVE_TAGS:
            self.problems.append(f"contenido activo <{tag}>")
        for name, value in attrs:
            value = value or ""
            if name.startswith("on"):
                self.problems.append(f"manejador de eventos {name}= en <{tag}>")
            if value.strip().lower().startswith("javascript:"):
                self.problems.append(f"URL javascript: en <{tag} {name}>")
                continue
            is_resource = name in RESOURCE_ATTRS or (tag == "link" and name == "href")
            if is_resource or name == "href":
                reason = classify(value, self.base, is_resource)
                if reason:
                    self.problems.append(f"<{tag} {name}>: {reason}")
            if name == "style":
                self.check_css(value)

    def check_css(self, css: str):
        for _, url in CSS_URL_RE.findall(css):
            reason = classify(url, self.base, resource=True)
            if reason:
                self.problems.append(f"url() en CSS: {reason}")

    def handle_data(self, data):
        if self.in_style:
            self.check_css(data)


def check_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    problems: list[str] = []
    if FILE_URL_RE.search(text):
        problems.append("contiene una URL file:")
    for match in sorted(set(USER_PATH_RE.findall(text)))[:5]:
        problems.append(f"contiene una ruta de usuario ({match})")
    home = str(Path.home())
    if len(home) > 1 and home in text:
        problems.append(f"contiene el directorio del usuario que compiló ({home})")
    scanner = Scanner(path.parent)
    scanner.feed(text)
    scanner.close()
    problems += scanner.problems
    if path.suffix == ".md":
        for ref in MD_IMAGE_RE.findall(text):
            reason = classify(ref, path.parent, resource=True)
            if reason:
                problems.append(f"imagen: {reason}")
    return list(dict.fromkeys(problems))


def collect(arg: str) -> list[Path]:
    path = Path(arg)
    if path.is_dir():
        found = sorted(p for p in path.iterdir() if p.is_file() and p.suffix in {".html", ".md"})
        if not found:
            raise Usage(f"{arg} no contiene archivos .html ni .md")
        return found
    if not path.is_file():
        raise Usage(f"{arg} no existe")
    if path.suffix not in {".html", ".md"}:
        raise Usage(f"{arg} no es un .html ni un .md")
    return [path]


def main(argv: list[str]) -> int:
    if not argv or argv[0] in {"-h", "--help"}:
        print(__doc__, file=sys.stderr if not argv else sys.stdout)
        return 2 if not argv else 0
    try:
        files = [f for arg in argv for f in collect(arg)]
    except Usage as exc:
        print(f"ERROR de uso: {exc}", file=sys.stderr)
        return 2
    failures = 0
    for path in files:
        for problem in check_file(path):
            print(f"ERROR: {path}: {problem}")
            failures += 1
    print(f"{len(files)} archivo(s) comprobado(s), {failures} problema(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
