"""Tests de manual-verifier/scripts/check_pii.py (mecanismo del check C13 «Datos personales» de manual-verifier/SKILL.md)."""

from __future__ import annotations

import os
import random
import shutil
import subprocess
import struct
import sys
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path

from fixtures import CHECK_PII, _chunk, COMPILE_PANDOC, COMPILE_PDF, PII_FICTITIOUS, PII_NEGATIVES, PII_POSITIVES, make_manual, png_bytes, write_section
from test_scripts import pandoc_args, run_script, script_args

INVENTORY = """---
borrador: false
---

## 1. Módulos y rutas

| Módulo | Ruta / Pantalla | Tipo de acceso | Roles que acceden | PII | Evidencia |
|--------|-----------------|----------------|-------------------|-----|-----------|
| Acceso | `/login` | público | todos | no | `routes.php:1` |
| Usuarios | `/usuarios` | autenticado | admin | sí | `routes.php:2` |
"""


def noisy_png(size: int = 48) -> bytes:
    rnd = random.Random(0)
    raw = b"".join(b"\x00" + bytes(rnd.randrange(256) for _ in range(size * 3)) for _ in range(size))
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", zlib.compress(raw)) + _chunk(b"IEND", b"")


def manifest(*rows: tuple[str, str, str]) -> str:
    lines = ["| Archivo | Sección | Pantalla | Estado | Enmascarado |", "|---|---|---|---|---|"]
    lines += [f"| {f} | S01 | {p} | OK | {e} |" for f, p, e in rows]
    return "---\ntotal_planificadas: 1\n---\n\n# Manifiesto de capturas\n\n" + "\n".join(lines) + "\n"


class PiiTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.m = make_manual(self.root)  # crea capturas/login.png
        write_section(self.m["secciones"], "S01-intro.md", "# Introducción\n\nPulse **Ingresar**.\n\n![login](../capturas/login.png)\n")
        (self.root / "03-inventario.md").write_text(INVENTORY, encoding="utf-8")
        self.write_manifest(("login.png", "/login", "no"))

    def write_manifest(self, *rows):
        (self.m["capturas"] / "MANIFIESTO.md").write_text(manifest(*rows), encoding="utf-8")

    def section(self, text: str, name: str = "S02-datos.md"):
        write_section(self.m["secciones"], name, f"# Datos\n\n{text}\n")

    def check(self, *args, path: str | None = None) -> subprocess.CompletedProcess:
        env = {**os.environ, **({"PATH": path} if path else {})}
        return subprocess.run(
            [sys.executable, str(CHECK_PII), *map(str, args or (self.root,))],
            capture_output=True, text=True, encoding="utf-8", env=env,
        )

    def assert_clean(self, **kwargs) -> subprocess.CompletedProcess:
        r = self.check(**kwargs)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r

    def assert_blocked(self, *fragments: str, **kwargs) -> subprocess.CompletedProcess:
        r = self.check(**kwargs)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        for fragment in fragments:
            self.assertIn(fragment, r.stdout)
        return r


class TestTextPatterns(PiiTestCase):
    def test_baseline_manual_without_personal_data_passes(self):
        self.assert_clean()

    def test_each_personal_data_pattern_blocks(self):
        for tipo, text, _ in PII_POSITIVES:
            with self.subTest(tipo=tipo, text=text):
                self.section(f"Ejemplo: {text}.")
                self.assert_blocked(f"S02-datos.md:3: {tipo}")

    def test_ordinary_manual_text_does_not_block(self):
        for text in PII_NEGATIVES:
            with self.subTest(text=text):
                self.section(text)
                self.assert_clean()

    def test_recognised_fictitious_data_does_not_block(self):
        for text in PII_FICTITIOUS:
            with self.subTest(text=text):
                self.section(f"Escriba {text} en el campo.")
                self.assert_clean()

    def test_every_occurrence_is_reported_not_just_the_first(self):
        self.section("ana@cliente.co\n\nluis@cliente.co\n\neva@cliente.co")
        r = self.assert_blocked()
        self.assertEqual(len([l for l in r.stdout.splitlines() if l.startswith("ERROR") and ": email" in l]), 3, r.stdout)

    def test_value_split_by_a_line_wrap_inside_a_paragraph_blocks(self):
        for tipo, text in (("documento", "con cédula\n1.023.456.789 registrada"), ("telefono", "llame al 300 123\n4567 hoy")):
            with self.subTest(tipo=tipo):
                self.section(text)
                self.assert_blocked(f"S02-datos.md:3: {tipo}")

    def test_report_never_reprints_the_full_value(self):
        self.section("Contacto: ana.perez@gmail.com")
        r = self.assert_blocked("email (an…om)")
        self.assertNotIn("ana.perez@gmail.com", r.stdout + r.stderr)


class TestPermittedValues(PiiTestCase):
    def test_public_contact_declared_with_a_reason_is_allowed_and_audited(self):
        self.section("Escriba a soporte@acme.co o llame al +57 601 555 1234.")
        self.assert_blocked("email", "telefono")
        (self.root / "pii-permitidos.txt").write_text(
            "# valor | motivo\nsoporte@acme.co | canal público de soporte del cliente\n+57 601 555 1234 | línea pública de soporte\n",
            encoding="utf-8",
        )
        r = self.assert_clean()
        self.assertIn("PERMITIDO:", r.stdout)
        self.assertIn("canal público de soporte del cliente", r.stdout)

    def test_permitted_value_without_a_reason_blocks(self):
        self.section("Escriba a soporte@acme.co.")
        (self.root / "pii-permitidos.txt").write_text("soporte@acme.co\n", encoding="utf-8")
        self.assert_blocked("pii-permitidos.txt:1")

    def test_permission_is_exact_not_a_domain_wildcard(self):
        self.section("Escriba a ana@acme.co.")
        (self.root / "pii-permitidos.txt").write_text("soporte@acme.co | soporte\n", encoding="utf-8")
        self.assert_blocked("email")


class TestCompiledOutputs(PiiTestCase):
    """Las salidas se generan con los scripts reales del compilador, no a mano."""

    def compile(self, to: str, name: str):
        out = self.root / "salida" / name
        r = run_script(COMPILE_PANDOC, pandoc_args(self.m, out, to))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return out

    @unittest.skipUnless(shutil.which("pandoc"), "pandoc no instalado")
    def test_clean_compiled_outputs_pass_including_embedded_images(self):
        # Captura con ruido: su base64 embebido en el HTML tiene tramos que, leídos como texto, parecen claves.
        (self.m["capturas"] / "login.png").write_bytes(noisy_png())
        for to, name in (("docx", "manual.docx"), ("html", "manual.html"), ("gfm", "manual.md")):
            self.compile(to, name)
        r = self.assert_clean()
        for name in ("manual.docx", "manual.html", "manual.md"):
            self.assertIn(name, r.stdout)  # positivo: cada salida se leyó

    @unittest.skipUnless(shutil.which("pandoc"), "pandoc no instalado")
    def test_personal_data_is_found_in_every_web_and_docx_output(self):
        self.section("Escriba a ana.perez@gmail.com.")
        for to, name in (("docx", "manual.docx"), ("html", "manual.html"), ("gfm", "manual.md")):
            self.compile(to, name)
        self.assert_blocked("S02-datos.md:3: email", "salida/manual.docx", "salida/manual.html", "salida/manual.md")

    @unittest.skipUnless(shutil.which("pandoc"), "pandoc no instalado")
    def test_value_wrapped_by_pandoc_in_the_html_output_blocks(self):
        # pandoc reparte el párrafo en líneas de 72 columnas: el número queda en la línea siguiente.
        self.section("En la lista aparece Ana (usuario@example.com, cédula 1.023.456.789).")
        out = self.compile("html", "manual.html")
        self.assertIn("cédula\n1.023.456.789", out.read_text(encoding="utf-8"))  # precondición: pandoc partió la línea
        r = self.assert_blocked()
        self.assertTrue([l for l in r.stdout.splitlines() if l.startswith("ERROR: salida/manual.html:") and ": documento" in l], r.stdout)

    @unittest.skipUnless(shutil.which("pandoc"), "pandoc no instalado")
    def test_personal_data_only_in_docx_metadata_blocks(self):
        out = self.compile("docx", "manual.docx")
        self.assert_clean()
        tampered = self.root / "t.docx"
        with zipfile.ZipFile(out) as src, zipfile.ZipFile(tampered, "w") as dst:
            for item in src.infolist():
                data = src.read(item)
                if item.filename == "docProps/core.xml":
                    data = data.replace(b"</cp:coreProperties>", b"<dc:creator>ana.perez@gmail.com</dc:creator></cp:coreProperties>")
                dst.writestr(item, data)
        tampered.replace(out)
        self.assert_blocked("salida/manual.docx", "email")

    @unittest.skipUnless(shutil.which("pandoc") and shutil.which("pdftotext"), "pandoc o pdftotext no instalados")
    def test_personal_data_is_found_in_the_pdf_text(self):
        self.section("Llame al 300 123 4567.")
        out = self.root / "salida" / "manual.pdf"
        r = run_script(COMPILE_PDF, script_args(self.m, out))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assert_blocked("salida/manual.pdf", "telefono")

    def test_pdf_that_cannot_be_read_blocks_instead_of_passing(self):
        (self.root / "salida").mkdir()
        (self.root / "salida" / "manual.pdf").write_bytes(b"%PDF-1.4 roto")
        bindir = self.root / "bin"
        bindir.mkdir()  # PATH sin pdftotext
        self.assert_blocked("salida/manual.pdf", path=str(bindir))


class TestScreenshotsManifest(PiiTestCase):
    def add_capture(self, name: str):
        (self.m["capturas"] / name).write_bytes(png_bytes())

    def test_pii_screen_masked_passes(self):
        self.add_capture("u.png")
        self.write_manifest(("login.png", "/login", "no"), ("u.png", "/usuarios", "sí"))
        self.assert_clean()

    def test_pii_screen_not_masked_blocks(self):
        self.add_capture("u.png")
        self.write_manifest(("login.png", "/login", "no"), ("u.png", "/usuarios", "no"))
        self.assert_blocked("u.png")

    def test_screen_name_with_backticks_matches_the_inventory_row(self):
        # La pantalla con PII la decide el inventario; el manifiesto sólo dice qué se hizo.
        self.add_capture("u.png")
        self.write_manifest(("login.png", "/login", "no"), ("u.png", "`/usuarios`", "no"))
        self.assert_blocked("u.png")

    def test_declared_exception_passes_and_is_audited(self):
        self.add_capture("u.png")
        self.write_manifest(("login.png", "/login", "no"), ("u.png", "/usuarios", "excepción: demo con datos sintéticos del cliente"))
        r = self.assert_clean()
        self.assertIn("EXCEPCIÓN:", r.stdout)
        self.assertIn("demo con datos sintéticos del cliente", r.stdout)

    def test_exception_without_reason_blocks(self):
        self.add_capture("u.png")
        self.write_manifest(("login.png", "/login", "no"), ("u.png", "/usuarios", "excepción:"))
        self.assert_blocked("u.png")

    def test_screen_missing_from_the_inventory_blocks(self):
        self.write_manifest(("login.png", "/perfil", "no"))
        self.assert_blocked("/perfil")

    def test_capture_without_a_manifest_row_blocks(self):
        self.add_capture("suelta.png")
        self.assert_blocked("suelta.png")

    def test_v1_inventory_without_pii_column_blocks(self):
        (self.root / "03-inventario.md").write_text(INVENTORY.replace(" PII |", " Notas |"), encoding="utf-8")
        self.assert_blocked("03-inventario.md")

    def test_v1_manifest_without_masking_column_blocks(self):
        (self.m["capturas"] / "MANIFIESTO.md").write_text(
            "| Archivo | Sección | Estado |\n|---|---|---|\n| login.png | S01 | OK |\n", encoding="utf-8"
        )
        self.assert_blocked("MANIFIESTO.md")

    def test_unknown_pii_value_in_inventory_blocks(self):
        (self.root / "03-inventario.md").write_text(INVENTORY.replace("| público | todos | no |", "| público | todos | quizá |"), encoding="utf-8")
        self.assert_blocked("/login")

    def test_unknown_pii_value_counts_as_pii(self):
        self.add_capture("u.png")
        self.write_manifest(("login.png", "/login", "no"), ("u.png", "/usuarios", "no"))
        (self.root / "03-inventario.md").write_text(INVENTORY.replace("| autenticado | admin | sí |", "| autenticado | admin | ? |"), encoding="utf-8")
        r = self.assert_blocked("/usuarios")
        self.assertIn("u.png: la pantalla /usuarios tiene PII", r.stdout)

    def test_missing_inventory_or_manifest_blocks(self):
        for victim in (self.root / "03-inventario.md", self.m["capturas"] / "MANIFIESTO.md"):
            with self.subTest(victim=victim.name):
                saved = victim.read_bytes()
                victim.unlink()
                self.assert_blocked(victim.name)
                victim.write_bytes(saved)


class TestUsage(PiiTestCase):
    def test_no_arguments_is_a_usage_error(self):
        r = subprocess.run([sys.executable, str(CHECK_PII)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)

    def test_missing_directory_or_secciones_is_a_usage_error(self):
        self.assertEqual(self.check(self.root / "no-existe").returncode, 2)
        shutil.rmtree(self.m["secciones"])
        self.assertEqual(self.check().returncode, 2)


if __name__ == "__main__":
    unittest.main()
