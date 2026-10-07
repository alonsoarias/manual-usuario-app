"""Helpers compartidos por los tests: manual mínimo en un directorio temporal.

Sin binarios en el repo: el PNG se genera desde bytes.
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "skills" / "manual-compiler" / "scripts"
CONCATENATE = SCRIPTS / "concatenate.py"
COMPILE_PANDOC = SCRIPTS / "compile_pandoc.sh"
COMPILE_PDF = SCRIPTS / "compile_pdf.sh"
PANDOC_FROM_FILE = SCRIPTS / "pandoc-from.txt"
CHECK_WEB_OUTPUT = REPO / "skills" / "manual-verifier" / "scripts" / "check_web_output.py"


def _chunk(tag: bytes, data: bytes) -> bytes:
    body = tag + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))


def png_bytes() -> bytes:
    """PNG válido de 1x1 píxel rojo."""
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    idat = zlib.compress(b"\x00\xff\x00\x00")
    return b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", idat) + _chunk(b"IEND", b"")


def make_manual(root: Path, brief: str | bytes | None = None) -> dict:
    """Crea secciones/, capturas/, 01-brief.md y 02-plan.md bajo `root`."""
    secciones = root / "secciones"
    capturas = root / "capturas"
    secciones.mkdir()
    capturas.mkdir()
    (capturas / "login.png").write_bytes(png_bytes())
    if brief is None:
        brief = "---\nnombre_comercial: Acme\nversion: 1.0\nfecha_corte: 2026-10-07\nidioma: es\n---\n"
    brief_path = root / "01-brief.md"
    if isinstance(brief, bytes):
        brief_path.write_bytes(brief)
    else:
        brief_path.write_text(brief, encoding="utf-8")
    plan = root / "02-plan.md"
    plan.write_text("# Plan\n", encoding="utf-8")
    return {"root": root, "secciones": secciones, "capturas": capturas, "brief": brief_path, "plan": plan}


def write_section(secciones: Path, name: str, content: str | bytes) -> Path:
    path = secciones / name
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8", newline="")
    return path


def concat_args(m: dict, output: Path) -> list[str]:
    return [
        "--secciones", str(m["secciones"]),
        "--capturas", str(m["capturas"]),
        "--plan", str(m["plan"]),
        "--brief", str(m["brief"]),
        "--output", str(output),
    ]
