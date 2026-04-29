#!/usr/bin/env python3
"""Concatena las secciones del manual en un único Markdown listo para Pandoc.

Lee el orden desde secciones/00-INDICE.md cuando existe; en su defecto, ordena
por nombre de archivo. Salta secciones de tipo `tabla-contenido-auto` (las
genera Pandoc/Typst). Ajusta rutas de imágenes a absolutas resolviendo desde
el directorio base del manual. Inyecta YAML front matter con metadatos del
brief.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

YAML_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
IMAGE_REF_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


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
    return path.read_text(encoding="utf-8")


def split_frontmatter(content: str) -> tuple[dict, str]:
    m = YAML_FRONTMATTER_RE.match(content)
    if not m:
        return {}, content
    frontmatter = parse_yaml_block(m.group(1))
    body = content[m.end():]
    return frontmatter, body


def list_section_files(secciones_dir: Path) -> list[Path]:
    """Devuelve la lista ordenada de secciones a concatenar.

    Si existe `00-INDICE.md` con líneas tipo `- S03-acceso.md`, las usa.
    En su defecto, ordena por nombre los `.md` excluyendo el índice.
    """
    indice = secciones_dir / "00-INDICE.md"
    if indice.exists():
        files: list[Path] = []
        for line in read_file(indice).splitlines():
            line = line.strip()
            m = re.match(r"^-\s+(.*\.md)\s*$", line)
            if m:
                candidate = secciones_dir / m.group(1)
                if candidate.exists():
                    files.append(candidate)
        if files:
            return files
    files = sorted(p for p in secciones_dir.glob("*.md") if p.name != "00-INDICE.md")
    return files


def adjust_image_paths(body: str, base_dir: Path, manual_root: Path) -> str:
    """Convierte rutas relativas de imágenes en absolutas resueltas desde manual_root."""
    def replace(match: re.Match) -> str:
        alt = match.group(1)
        url = match.group(2).strip()
        if url.startswith(("http://", "https://", "/")):
            return match.group(0)
        candidate_a = (base_dir / url).resolve()
        candidate_b = (manual_root / url).resolve()
        if candidate_a.exists():
            resolved = candidate_a
        elif candidate_b.exists():
            resolved = candidate_b
        else:
            resolved = candidate_b
        return f"![{alt}]({resolved})"
    return IMAGE_REF_RE.sub(replace, body)


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


def build_pandoc_yaml(meta: dict) -> str:
    lines = ["---"]
    lines.append(f"title: \"{meta.get('title', 'Manual de usuario')}\"")
    if meta.get("subtitle"):
        lines.append(f"subtitle: \"{meta['subtitle']}\"")
    if meta.get("version"):
        lines.append(f"version: \"{meta['version']}\"")
    if meta.get("date"):
        lines.append(f"date: \"{meta['date']}\"")
    if meta.get("lang"):
        lines.append(f"lang: \"{meta['lang']}\"")
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
    files = list_section_files(secciones)
    if not files:
        print("ERROR: no se encontraron secciones para concatenar", file=sys.stderr)
        return 2

    meta = extract_brief_metadata(brief)
    output.parent.mkdir(parents=True, exist_ok=True)

    skipped = 0
    written = 0
    with output.open("w", encoding="utf-8") as out:
        out.write(build_pandoc_yaml(meta))
        for path in files:
            text = read_file(path)
            fm, body = split_frontmatter(text)
            tipo = (fm.get("tipo") or "").strip()
            if tipo == "tabla-contenido-auto":
                skipped += 1
                continue
            body = adjust_image_paths(body, path.parent, manual_root)
            out.write("\n\n")
            out.write(body.lstrip("\n"))
            written += 1

    print(f"Secciones escritas: {written}")
    print(f"Secciones omitidas (tabla-contenido-auto): {skipped}")
    print(f"Salida: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
