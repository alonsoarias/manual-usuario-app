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
CHECK_PII = REPO / "skills" / "manual-verifier" / "scripts" / "check_pii.py"
PII_MASKING_MD = REPO / "skills" / "screenshot-capturer" / "references" / "pii-masking.md"

# Corpus común al script de enmascarado (JS, pii-masking.md) y al check C13 (Python, check_pii.py):
# los dos deben coincidir en qué es un dato personal. (tipo, texto en la página, fragmento sensible).
PII_POSITIVES = [
    ("email", "ana.perez@gmail.com", "ana.perez@gmail.com"),
    ("email", "luis.gomez@cliente.co", "luis.gomez@cliente.co"),
    ("email", "eva@cliente.co", "eva@cliente.co"),
    ("telefono", "+57 300 123 4567", "300 123 4567"),
    ("telefono", "Móvil 300 123 4568", "300 123 4568"),
    ("telefono", "612 345 678", "612 345 678"),
    ("telefono", "(601) 234 5678", "234 5678"),
    ("telefono", "3001234567", "3001234567"),
    ("telefono", "Celular Nº3001234569", "3001234569"),  # º es letra Unicode: exige \w ASCII como en JS
    ("documento", "Cédula: 1.023.456.789", "1.023.456.789"),
    ("documento", "Titular 12345678Z", "12345678Z"),
    ("documento", "Titular X1234567L", "X1234567L"),
    ("documento", "Titular 123.456.789-09", "123.456.789-09"),
    ("documento", "Titular 123-45-6789", "123-45-6789"),
    ("documento", "DNI: 87654321", "87654321"),
    ("tarjeta", "4539 1488 0343 6467", "4539 1488 0343 6467"),
    ("tarjeta", "4539148803436467", "4539148803436467"),
    ("iban", "ES91 2100 0418 4502 0005 1332", "2100 0418 4502 0005 1332"),
    ("token", "sk_" + "live_4eC39HqLyjWDarjtT1zdp7dc", "4eC39HqLyjWDarjtT1zdp7dc"),
    ("token", "ghp_16C7e42F292c6912E7710c838347Ae178B4a", "16C7e42F292c6912E7710c838347Ae178B4a"),
    ("token", "AKIAIOSFODNN7EXAMPLE", "AKIAIOSFODNN7EXAMPLE"),
    ("token", "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U", "dozjgNryP4J3jVmNHl0w5N"),
    ("token", "Zx8KqP2mN7vR4tY9wL3sB6hJ1cF5gD0aE", "Zx8KqP2mN7vR4tY9wL3sB6hJ1cF5gD0aE"),
]

# Texto habitual de un manual que NO es un dato personal: ni se enmascara ni bloquea C13.
PII_NEGATIVES = [
    "Versión 2.4.1",
    "Corte 2026-10-07",
    "Último acceso 2026-10-07 14:30",
    "Servidor 192.168.10.200",
    "Total $1.500.000",
    "Viewport 1366x768",
    "S05-paso-3-clic-guardar-boton-principal.png",
    "Pulse Guardar y continuar",
    "Paso 3 de 12",
    "Pedido 12345678",
    "4539 1488 0343 6468",  # no pasa Luhn
    "ES91 2100 0418 4502 0005 1333",  # dígito de control IBAN inválido
]

# Datos ficticios reconocidos: el JS los enmascara igual (inofensivo); C13 no bloquea por ellos.
PII_FICTITIOUS = [
    "usuario@example.com",
    "ana@soporte.example.org",
    "demo@app.test",
    "+1 (555) 555-0199",
    "07700 900123",
    "4111 1111 1111 1111",
    "000 000 0000",
    "GB82 WEST 1234 5698 7654 32",
]


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
