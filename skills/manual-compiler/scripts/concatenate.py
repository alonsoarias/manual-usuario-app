#!/usr/bin/env python3
"""Concatena las secciones del manual en un único Markdown listo para Pandoc.

Lee el orden desde secciones/00-INDICE.md cuando existe; en su defecto, ordena
por nombre de archivo. Salta secciones de tipo `tabla-contenido-auto` (las
genera Pandoc/Typst). Ajusta rutas de imágenes a absolutas resolviendo desde
el directorio base del manual. Inyecta YAML front matter con metadatos del
brief.

Seguridad: el Markdown lo redactan agentes a partir de la app analizada y no es de confianza. Las
imágenes se reescriben a rutas absolutas y luego se VALIDAN sobre el AST de pandoc (lo que pandoc
resolverá de verdad: imágenes en línea, de referencia, en tablas, en metadatos). Toda imagen local
debe resolverse (realpath) dentro del ancestro común de secciones/ y capturas/. Limitación: realpath
no detecta enlaces duros (hardlinks); un hardlink a un archivo ajeno dentro del manual pasa.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
from pathlib import Path

# El cierre `---` admite fin de archivo (stub sin `\n` final) y bloque vacío.
YAML_FRONTMATTER_RE = re.compile(r"^---\n(.*?)^---[ \t]*(?:\n|\Z)", re.DOTALL | re.MULTILINE)
# Imagen remota o embebida: no se toca. Cualquier otro esquema (`file:`...) lo rechaza la validación.
REMOTE_URL_RE = re.compile(r"^(?:https?:|data:|//)", re.IGNORECASE)
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
# ÚNICA fuente del `--from` de pandoc: la leen esta validación y los cuatro pandoc de los scripts shell
# (DOCX, Typst, XeLaTeX, pdfLaTeX). Validar con otras extensiones que las del motor deja imágenes sin ver
# (p. ej. con `$..$` como matemática una imagen puede quedar oculta dentro de un nodo Math).
PANDOC_FROM = Path(__file__).with_name("pandoc-from.txt").read_text(encoding="utf-8").strip()
# destino de la imagen + título opcional (`"t"` o `'t'`), que no forma parte de la ruta
IMAGE_REF_RE = re.compile(r"!\[([^\]]*)\]\(\s*([^)\s]+)(\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)")


def parse_yaml_block(text: str) -> dict:
    """Parsea un bloque YAML simple clave: valor (sin dependencia externa).

    Soporta: cadenas, números, booleanos, listas inline `[a, b]` y bloques
    multivalor con `-`. Valores con comillas se desempaquetan. No es un
    parser YAML completo: cubre el subset usado por el plugin.
    """
    data: dict = {}
    current_list_key: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line or line.startswith("#"):
            continue
        if current_list_key and line.startswith("  -"):
            value = line[3:].strip().strip('"').strip("'")
            data.setdefault(current_list_key, []).append(value)
            continue
        current_list_key = None
        m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.*)$", line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        if value == "":
            current_list_key = key
            data[key] = []
            continue
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1]
            data[key] = [v.strip().strip('"').strip("'") for v in inner.split(",") if v.strip()]
            continue
        if value.lower() in ("true", "false"):
            data[key] = value.lower() == "true"
            continue
        try:
            if "." in value:
                data[key] = float(value)
            else:
                data[key] = int(value)
            continue
        except ValueError:
            pass
        data[key] = value.strip('"').strip("'")
    return data


def read_file(path: Path) -> str:
    # utf-8-sig quita el BOM de editores de Windows; read_text ya normaliza CRLF a \n.
    return path.read_text(encoding="utf-8-sig")


def split_frontmatter(content: str) -> tuple[dict, str]:
    m = YAML_FRONTMATTER_RE.match(content)
    if not m:
        return {}, content
    frontmatter = parse_yaml_block(m.group(1))
    body = content[m.end():]
    return frontmatter, body


class UnsafePath(Exception):
    """Una ruta del contenido (redactado por agentes) apunta fuera del manual."""


def is_safe_section(path: Path, secciones_dir: Path, label: str) -> bool:
    """Una sección es un archivo dentro de secciones/, sin enlaces simbólicos ni rutas que escapen."""
    if path.is_symlink() or secciones_dir.resolve() not in path.resolve().parents:
        print(f"AVISO: {label} es un enlace simbólico o queda fuera de secciones/; se omite", file=sys.stderr)
        return False
    return True


def list_section_files(secciones_dir: Path) -> list[Path]:
    """Devuelve la lista ordenada de secciones a concatenar.

    Si existe `00-INDICE.md` con líneas tipo `- S03-acceso.md`, las usa.
    En su defecto, ordena por nombre los `.md` excluyendo el índice.
    """
    indice = secciones_dir / "00-INDICE.md"
    if indice.exists():
        files: list[Path] = []
        for line in read_file(indice).splitlines():
            m = re.match(r"^-\s+(.*\.md)\s*$", line.strip())
            if not m:
                continue
            name = m.group(1)
            candidate = secciones_dir / name
            if not is_safe_section(candidate, secciones_dir, name):
                continue
            if candidate.exists():
                files.append(candidate.resolve())
            else:
                print(f"AVISO: 00-INDICE.md lista {name}, que no existe; se omite", file=sys.stderr)
        if files:
            for p in sorted(secciones_dir.glob("*.md")):
                if p.name != "00-INDICE.md" and not p.is_symlink() and p.resolve() not in files:
                    print(f"AVISO: {p.name} no está en 00-INDICE.md; se omite", file=sys.stderr)
            return files
        print("AVISO: 00-INDICE.md sin entradas válidas; orden alfabético", file=sys.stderr)
    return [
        p for p in sorted(secciones_dir.glob("*.md"))
        if p.name != "00-INDICE.md" and is_safe_section(p, secciones_dir, p.name)
    ]


def decode_local_url(url: str) -> str:
    """Decodifica una URL de imagen local una sola vez (como pandoc); rechaza lo ambiguo."""
    try:
        decoded = urllib.parse.unquote(url, errors="strict")
    except UnicodeDecodeError as exc:
        raise UnsafePath(f"ruta de imagen con codificación inválida: {url!r}") from exc
    if "%" in decoded or any(c in decoded for c in "\x00\r\n"):
        raise UnsafePath(f"ruta de imagen con doble codificación, NUL o salto de línea: {url!r}")
    return decoded


def adjust_image_paths(body: str, base_dir: Path, manual_root: Path, sandbox_root: Path) -> str:
    """Reescribe las imágenes en línea locales a rutas absolutas (codificadas como URL).

    No decide qué es seguro: eso lo hace `validate_images` sobre el AST del documento final.
    """
    def replace(match: re.Match) -> str:
        alt = match.group(1)
        url = match.group(2)
        title = match.group(3) or ""
        if REMOTE_URL_RE.match(url) or SCHEME_RE.match(url):
            return match.group(0)
        if "?" in url or "#" in url:
            raise UnsafePath(f"ruta de imagen con consulta o fragmento: {url}")
        path = decode_local_url(url)
        try:
            if path.startswith("/"):
                resolved = Path(path).resolve()
            else:
                candidates = [(base_dir / path).resolve(), (manual_root / path).resolve()]
                # la que exista; si ninguna (la detectará el verificador), la que quede dentro del manual
                resolved = next((c for c in candidates if c.exists()), None) or next(
                    (c for c in reversed(candidates) if sandbox_root in c.parents), candidates[1]
                )
        except (ValueError, OSError) as exc:
            raise UnsafePath(f"ruta de imagen no resoluble: {url}: {exc}") from exc
        return f"![{alt}]({urllib.parse.quote(str(resolved), safe='/')}{title})"
    return IMAGE_REF_RE.sub(replace, body)


def image_urls(node):
    """Todas las URLs de nodos Image del AST de pandoc (cuerpo, tablas, figuras, metadatos)."""
    if isinstance(node, dict):
        if node.get("t") == "Image":
            yield node["c"][2][0]
        for value in node.values():
            yield from image_urls(value)
    elif isinstance(node, list):
        for item in node:
            yield from image_urls(item)


def check_image_url(url: str, sandbox_root: Path) -> None:
    if REMOTE_URL_RE.match(url):
        return
    if SCHEME_RE.match(url):
        raise UnsafePath(f"imagen con esquema no admitido: {url!r}")
    path = Path(decode_local_url(url))
    if not path.is_absolute():
        raise UnsafePath(
            f"imagen con ruta relativa sin reescribir: {url!r}; use ![alt](ruta) en línea "
            "(espacios como %20) o una ruta absoluta dentro del manual"
        )
    try:
        real = path.resolve()
    except (ValueError, OSError) as exc:
        raise UnsafePath(f"ruta de imagen no resoluble: {url!r}: {exc}") from exc
    # real != path: la ruta lleva `..` o enlaces simbólicos; no se acepta aunque acabe dentro
    if real != path or sandbox_root not in real.parents:
        raise UnsafePath(f"imagen fuera del manual ({sandbox_root}) o ruta no canónica: {url!r}")


def validate_images(markdown: str, sandbox_root: Path) -> None:
    """Fail-closed: valida las imágenes tal como las resolverá pandoc, no según la sintaxis del texto."""
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        raise UnsafePath("pandoc no está en PATH: sin él no se pueden validar las imágenes del manual")
    proc = subprocess.run(
        [pandoc, "--from", PANDOC_FROM, "--to", "json"],
        input=markdown.encode("utf-8"), capture_output=True, check=False,
    )
    if proc.returncode != 0:
        raise UnsafePath(f"pandoc no pudo analizar el Markdown: {proc.stderr.decode('utf-8', 'replace').strip()}")
    for url in image_urls(json.loads(proc.stdout)):
        check_image_url(url, sandbox_root)


def extract_brief_metadata(brief_path: Path) -> dict:
    """Extrae los campos clave del brief para inyectarlos en el front matter."""
    if not brief_path.exists():
        return {}
    text = read_file(brief_path)
    fm, _ = split_frontmatter(text)
    return {
        "title": str(fm.get("nombre_comercial", "Manual de usuario")),
        "subtitle": "Manual de usuario",
        "version": str(fm.get("version", "")),
        "date": str(fm.get("fecha_corte", "")),
        "lang": str(fm.get("idioma", "es")),
        "audience": str((fm.get("audiencia") or {}).get("perfil", "")) if isinstance(fm.get("audiencia"), dict) else "",
    }


def yaml_str(value: object) -> str:
    """Escalar YAML entre comillas dobles; JSON es un subconjunto válido y escapa `"` y `\\`."""
    return json.dumps(str(value), ensure_ascii=False)


def build_pandoc_yaml(meta: dict) -> str:
    lines = ["---"]
    lines.append(f"title: {yaml_str(meta.get('title', 'Manual de usuario'))}")
    for key in ("subtitle", "version", "date", "lang"):
        if meta.get(key):
            lines.append(f"{key}: {yaml_str(meta[key])}")
    lines.append("toc: true")
    lines.append("toc-depth: 3")
    lines.append("numbersections: true")
    lines.append("---\n")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Concatena secciones de manual a Markdown único.")
    parser.add_argument("--secciones", required=True, help="Directorio con las secciones .md")
    parser.add_argument("--capturas", required=True, help="Directorio con las capturas (no se altera)")
    parser.add_argument("--plan", required=True, help="Ruta a 02-plan.md")
    parser.add_argument("--brief", required=True, help="Ruta a 01-brief.md")
    parser.add_argument("--output", required=True, help="Archivo Markdown concatenado de salida")
    args = parser.parse_args()

    secciones = Path(args.secciones).resolve()
    capturas = Path(args.capturas).resolve()
    plan = Path(args.plan).resolve()
    brief = Path(args.brief).resolve()
    output = Path(args.output).resolve()

    if not secciones.is_dir():
        print(f"ERROR: secciones/ no es un directorio: {secciones}", file=sys.stderr)
        return 2
    if not plan.exists() or not brief.exists():
        print("ERROR: faltan plan o brief", file=sys.stderr)
        return 2
    if not capturas.is_dir():
        print(f"ERROR: capturas/ no es un directorio: {capturas}", file=sys.stderr)
        return 2

    manual_root = secciones.parent
    sandbox_root = Path(os.path.commonpath([secciones, capturas]))
    files = list_section_files(secciones)
    if not files:
        print("ERROR: no se encontraron secciones para concatenar", file=sys.stderr)
        return 2

    meta = extract_brief_metadata(brief)
    output.parent.mkdir(parents=True, exist_ok=True)

    skipped = 0
    parts: list[str] = []
    try:
        for path in files:
            fm, body = split_frontmatter(read_file(path))
            if (fm.get("tipo") or "").strip() == "tabla-contenido-auto":
                skipped += 1
                continue
            parts.append("\n\n" + adjust_image_paths(body, path.parent, manual_root, sandbox_root).lstrip("\n"))
        document = build_pandoc_yaml(meta) + "".join(parts)
        validate_images(document, sandbox_root)
    except UnsafePath as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    written = len(parts)
    output.write_text(document, encoding="utf-8")

    print(f"Secciones escritas: {written}")
    print(f"Secciones omitidas (tabla-contenido-auto): {skipped}")
    print(f"Salida: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
