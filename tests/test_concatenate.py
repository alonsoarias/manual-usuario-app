"""Tests de concatenate.py: se ejecuta como proceso real (el punto de entrada de producción)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from fixtures import CONCATENATE, REPO, concat_args, make_manual, write_section

STUB_AUTO = "---\ntipo: tabla-contenido-auto\n---\n"


def run_concat(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CONCATENATE), *args], capture_output=True, text=True, encoding="utf-8"
    )


def header_lines(text: str) -> list[str]:
    assert text.startswith("---\n"), text[:40]
    return text[4 : text.index("\n---\n", 4)].splitlines()


class ConcatenateTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def build(self, brief=None):
        self.m = make_manual(self.root, brief)
        self.out = self.root / "salida" / "concat.md"
        return self.m

    def concat(self) -> str:
        r = run_concat(concat_args(self.m, self.out))
        self.assertEqual(r.returncode, 0, r.stderr)
        return self.out.read_text(encoding="utf-8")


class TestOrder(ConcatenateTestCase):
    def test_index_order_wins_over_glob_order(self):
        self.build()
        write_section(self.m["secciones"], "S01-a.md", "AAA\n")
        write_section(self.m["secciones"], "S02-b.md", "BBB\n")
        write_section(self.m["secciones"], "00-INDICE.md", "# Índice\n\n- S02-b.md\n- S01-a.md\n")
        text = self.concat()
        self.assertLess(text.index("BBB"), text.index("AAA"))

    def test_without_index_falls_back_to_glob_order(self):
        self.build()
        write_section(self.m["secciones"], "S02-b.md", "BBB\n")
        write_section(self.m["secciones"], "S01-a.md", "AAA\n")
        text = self.concat()
        self.assertLess(text.index("AAA"), text.index("BBB"))

    def test_index_itself_is_never_concatenated(self):
        self.build()
        write_section(self.m["secciones"], "S01-a.md", "AAA\n")
        write_section(self.m["secciones"], "00-INDICE.md", "# Índice\n\n- S01-a.md\n")
        self.assertNotIn("# Índice", self.concat())

    def test_index_entry_pointing_to_a_missing_file_is_reported(self):
        # Antes se descartaba en silencio y el manual salía sin esa sección.
        self.build()
        write_section(self.m["secciones"], "S01-a.md", "AAA\n")
        write_section(self.m["secciones"], "00-INDICE.md", "- S01-a.md\n- S02-fantasma.md\n")
        r = run_concat(concat_args(self.m, self.out))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("S02-fantasma.md", r.stderr)

    def test_section_missing_from_the_index_is_reported(self):
        self.build()
        write_section(self.m["secciones"], "S01-a.md", "AAA\n")
        write_section(self.m["secciones"], "S02-b.md", "BBB\n")
        write_section(self.m["secciones"], "00-INDICE.md", "- S01-a.md\n")
        r = run_concat(concat_args(self.m, self.out))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("S02-b.md", r.stderr)

    def test_index_format_documented_in_manual_writer_is_the_one_parsed(self):
        # El ejemplo del SKILL se extrae del documento: si el formato documentado deja de parsearse, cae.
        skill = (REPO / "skills" / "manual-writer" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("## Formato de `secciones/00-INDICE.md`", skill)
        heading = skill.index("## Formato de `secciones/00-INDICE.md`")
        block = skill[heading:].split("```markdown\n", 1)[1].split("```", 1)[0]
        names = [l[2:].strip() for l in block.splitlines() if l.startswith("- ")]
        self.assertGreaterEqual(len(names), 3, block)
        self.build()
        for name in reversed(names):  # creados al revés: el orden sólo puede venir del índice
            body = STUB_AUTO if "tabla-contenido-auto" in name else f"MARK-{name}\n"
            write_section(self.m["secciones"], name, body)
        write_section(self.m["secciones"], "00-INDICE.md", block)
        # centinela: sólo se deja fuera si el índice documentado se parseó (el orden por glob coincide con el del ejemplo)
        write_section(self.m["secciones"], "ZZ-fuera-del-indice.md", "MARK-FUERA\n")
        r = run_concat(concat_args(self.m, self.out))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("ZZ-fuera-del-indice.md", r.stderr)
        text = self.out.read_text(encoding="utf-8")
        self.assertNotIn("MARK-FUERA", text)
        marks = [f"MARK-{n}" for n in names if "tabla-contenido-auto" not in n]
        self.assertEqual([text.index(m) for m in marks], sorted(text.index(m) for m in marks))
        self.assertTrue(all(m in text for m in marks))

    def test_index_entries_escaping_secciones_are_rejected(self):
        self.build()
        write_section(self.m["secciones"], "S01-a.md", "AAA\n")
        (self.root / "fuera.md").write_text("FUERA-RELATIVA\n", encoding="utf-8")
        absolute = self.root / "absoluta.md"
        absolute.write_text("FUERA-ABSOLUTA\n", encoding="utf-8")
        write_section(self.m["secciones"], "00-INDICE.md", f"- S01-a.md\n- ../fuera.md\n- {absolute}\n")
        r = run_concat(concat_args(self.m, self.out))
        self.assertEqual(r.returncode, 0, r.stderr)
        text = self.out.read_text(encoding="utf-8")
        self.assertIn("AAA", text)
        self.assertNotIn("FUERA-RELATIVA", text)
        self.assertNotIn("FUERA-ABSOLUTA", text)
        self.assertIn("../fuera.md", r.stderr)
        self.assertIn(str(absolute), r.stderr)

    def test_index_without_valid_entries_warns_and_uses_alphabetical_order(self):
        self.build()
        write_section(self.m["secciones"], "S02-b.md", "BBB\n")
        write_section(self.m["secciones"], "S01-a.md", "AAA\n")
        write_section(self.m["secciones"], "00-INDICE.md", "1. S02-b.md\n2. S01-a.md\n")
        r = run_concat(concat_args(self.m, self.out))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("00-INDICE.md sin entradas válidas", r.stderr)
        text = self.out.read_text(encoding="utf-8")
        self.assertLess(text.index("AAA"), text.index("BBB"))

    def test_auto_toc_section_is_skipped(self):
        self.build()
        write_section(self.m["secciones"], "S01-toc.md", STUB_AUTO + "\nTOCBODY\n")
        write_section(self.m["secciones"], "S02-a.md", "AAA\n")
        r = run_concat(concat_args(self.m, self.out))
        text = self.out.read_text(encoding="utf-8")
        self.assertNotIn("TOCBODY", text)
        self.assertIn("AAA", text)
        self.assertIn("omitidas (tabla-contenido-auto): 1", r.stdout)

    def test_auto_toc_stub_without_trailing_newline_is_skipped(self):
        # El writer permite «stub vacío con sólo frontmatter»; un editor puede no dejar \n final.
        self.build()
        write_section(self.m["secciones"], "S01-toc.md", "---\ntipo: tabla-contenido-auto\n---")
        write_section(self.m["secciones"], "S02-a.md", "AAA\n")
        text = self.concat()
        self.assertNotIn("tabla-contenido-auto", text)

    def test_auto_toc_section_with_crlf_frontmatter_is_skipped(self):
        self.build()
        write_section(
            self.m["secciones"], "S01-toc.md", b"---\r\ntipo: tabla-contenido-auto\r\n---\r\n\r\nTOCBODY\r\n"
        )
        write_section(self.m["secciones"], "S02-a.md", "AAA\n")
        text = self.concat()
        self.assertNotIn("TOCBODY", text)
        self.assertNotIn("tabla-contenido-auto", text)

    def test_auto_toc_section_with_bom_is_skipped(self):
        # Editores de Windows guardan UTF-8 con BOM: antes de `---`, el frontmatter no se reconocía.
        self.build()
        write_section(
            self.m["secciones"], "S01-toc.md", b"\xef\xbb\xbf---\ntipo: tabla-contenido-auto\n---\n\nTOCBODY\n"
        )
        write_section(self.m["secciones"], "S02-a.md", "AAA\n")
        text = self.concat()
        self.assertNotIn("TOCBODY", text)
        self.assertIn("AAA", text)


class TestImagePaths(ConcatenateTestCase):
    def image_target(self, text: str) -> str:
        return text[text.index("](") + 2 : text.index(")", text.index("]("))]

    def test_relative_to_section_dir_becomes_absolute(self):
        self.build()
        write_section(self.m["secciones"], "S01-a.md", "![login](../capturas/login.png)\n")
        target = self.image_target(self.concat())
        self.assertEqual(Path(target), (self.m["capturas"] / "login.png").resolve())

    def test_relative_to_manual_root_becomes_absolute(self):
        self.build()
        write_section(self.m["secciones"], "S01-a.md", "![login](capturas/login.png)\n")
        target = self.image_target(self.concat())
        self.assertEqual(Path(target), (self.m["capturas"] / "login.png").resolve())

    def test_data_uri_images_are_left_untouched(self):
        self.build()
        uri = "data:image/png;base64,AAAA"
        write_section(self.m["secciones"], "S01-a.md", f"![x]({uri})\n")
        self.assertIn(f"![x]({uri})", self.concat())

    def test_remote_images_are_rejected_because_pandoc_would_download_them(self):
        # pandoc descarga las imágenes remotas al compilar (HTML y DOCX): SSRF + incrustación en la salida
        self.build()
        for url in ("https://example.com/a.png", "http://127.0.0.1:9/a.png", "HTTP://H/A.PNG", "//cdn.example.com/a.png"):
            with self.subTest(url=url):
                write_section(self.m["secciones"], "S01-a.md", f"![x]({url})\n")
                r = run_concat(concat_args(self.m, self.out))
                self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
                self.assertIn("imagen remota", r.stderr)
                self.assertNotIn("Traceback", r.stderr)
                self.assertFalse(self.out.exists())

    def test_optional_image_title_does_not_end_up_in_the_path(self):
        self.build()
        write_section(self.m["secciones"], "S01-a.md", '![login](../capturas/login.png "Pantalla de acceso")\n')
        text = self.concat()
        target = self.image_target(text)
        self.assertEqual(Path(target.split(' "')[0]), (self.m["capturas"] / "login.png").resolve())
        self.assertIn('"Pantalla de acceso"', text)

    @unittest.skipUnless(shutil.which("pandoc"), "pandoc no instalado")
    def test_image_in_directory_with_spaces_resolves_in_pandoc(self):
        self.root = self.root / "mi manual"
        self.root.mkdir()
        self.build()
        write_section(self.m["secciones"], "S01-a.md", "![login](../capturas/login.png)\n")
        self.concat()
        r = subprocess.run(
            ["pandoc", str(self.out), "-t", "html", "--embed-resources", "--standalone"],
            capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("Could not fetch resource", r.stderr)
        self.assertIn("data:image/png;base64", r.stdout)


class TestFrontmatterTitle(ConcatenateTestCase):
    def build_with_section(self, brief):
        self.build(brief)
        write_section(self.m["secciones"], "S01-a.md", "AAA\n")

    def title_line(self, text: str) -> str:
        (line,) = [l for l in header_lines(text) if l.startswith("title:")]
        value = line[len("title:"):].strip()
        try:
            # un escalar YAML entre comillas dobles es JSON válido si sólo usa escapes comunes
            return json.loads(value)
        except json.JSONDecodeError:
            self.fail(f"title no es un escalar YAML entre comillas bien formado: {line!r}")

    def test_title_with_double_quotes_stays_a_valid_yaml_string(self):
        self.build_with_section('---\nnombre_comercial: Acme "Pro" Suite\nidioma: es\n---\n')
        self.assertEqual(self.title_line(self.concat()), 'Acme "Pro" Suite')

    def test_title_with_backslash_stays_a_valid_yaml_string(self):
        self.build_with_section("---\nnombre_comercial: C:\\Acme\nidioma: es\n---\n")
        self.assertEqual(self.title_line(self.concat()), "C:\\Acme")

    @unittest.skipUnless(shutil.which("pandoc"), "pandoc no instalado")
    def test_pandoc_reads_title_with_quotes_back_unchanged(self):
        self.build_with_section('---\nnombre_comercial: Acme "Pro" Suite\nidioma: es\n---\n')
        self.concat()
        tpl = self.root / "t.txt"
        tpl.write_text("$title$", encoding="utf-8")
        r = subprocess.run(
            ["pandoc", str(self.out), "-f", "markdown-smart", "-t", "plain", f"--template={tpl}"],
            capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), 'Acme "Pro" Suite')

    def test_brief_with_crlf_frontmatter_keeps_its_metadata(self):
        self.build_with_section(b"---\r\nnombre_comercial: Acme\r\nversion: 2.0\r\nidioma: en\r\n---\r\n")
        text = self.concat()
        self.assertEqual(self.title_line(text), "Acme")
        self.assertIn('lang: "en"', header_lines(text))

    def test_brief_with_bom_keeps_its_metadata(self):
        self.build_with_section(b"\xef\xbb\xbf---\nnombre_comercial: Acme\nidioma: en\n---\n")
        text = self.concat()
        self.assertEqual(self.title_line(text), "Acme")
        self.assertIn('lang: "en"', header_lines(text))


def header_value(text: str, key: str) -> str:
    (line,) = [l for l in header_lines(text) if l.startswith(f"{key}:")]
    return json.loads(line[len(key) + 1 :].strip())


class TestLanguageLabels(ConcatenateTestCase):
    """El subtítulo y el título de la TOC salen de una tabla por idioma, no de literales en español."""

    EXPECTED = {
        "es": ("Manual de usuario", "Tabla de contenido"),
        "en": ("User manual", "Table of contents"),
        "pt": ("Manual do usuário", "Índice"),
    }

    def build_lang(self, lang: str | None):
        line = f"idioma: {lang}\n" if lang is not None else ""
        self.build(f"---\nnombre_comercial: Acme\n{line}---\n")
        write_section(self.m["secciones"], "S01-a.md", "AAA\n")

    def test_subtitle_and_toc_title_follow_the_language(self):
        for lang, (subtitle, toc_title) in self.EXPECTED.items():
            with self.subTest(lang=lang):
                self.root = self.root / lang
                self.root.mkdir()
                self.build_lang(lang)
                text = self.concat()
                self.assertEqual(header_value(text, "subtitle"), subtitle)
                self.assertEqual(header_value(text, "toc-title"), toc_title)
                self.assertEqual(header_value(text, "lang"), lang)

    def test_region_and_case_are_ignored_when_choosing_labels(self):
        for lang in ("en-US", "EN", "pt-BR"):
            with self.subTest(lang=lang):
                self.root = self.root / lang
                self.root.mkdir()
                self.build_lang(lang)
                text = self.concat()
                self.assertEqual(header_value(text, "subtitle"), self.EXPECTED[lang[:2].lower()][0])
                self.assertEqual(header_value(text, "lang"), lang)  # el valor del brief no se reescribe

    def test_missing_language_defaults_to_spanish(self):
        self.build_lang(None)
        self.assertEqual(header_value(self.concat(), "subtitle"), "Manual de usuario")

    def test_unsupported_language_is_a_clear_error(self):
        # fail-closed: un manual en francés con subtítulo en español sería un error silencioso en la entrega
        for lang in ("fr", "klingon", "xx"):
            with self.subTest(lang=lang):
                self.root = self.root / lang
                self.root.mkdir()
                self.build_lang(lang)
                r = run_concat(concat_args(self.m, self.out))
                self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
                self.assertIn("idioma", r.stderr)
                self.assertIn(lang, r.stderr)
                for supported in ("es", "en", "pt"):
                    self.assertIn(supported, r.stderr)
                self.assertNotIn("Traceback", r.stderr)
                self.assertFalse(self.out.exists())


class TestLinksAreNeverExecutable(ConcatenateTestCase):
    """Un enlace o autolink con esquema ejecutable sale con el href vivo en HTML: mismo AST que las imágenes, mismo fail-closed."""

    def run_with_link(self, snippet: str) -> subprocess.CompletedProcess:
        self.build()
        write_section(self.m["secciones"], "S01-a.md", f"Antes.\n\n{snippet}\n\nDespués.\n")
        return run_concat(concat_args(self.m, self.out))

    def assert_rejected(self, snippet: str, fragment: str | None = None):
        r = self.run_with_link(snippet)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        self.assertFalse(self.out.exists())
        if fragment:
            self.assertIn(fragment, r.stderr)

    def assert_accepted(self, snippet: str):
        r = self.run_with_link(snippet)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("Después.", self.out.read_text(encoding="utf-8"))

    def test_javascript_scheme_link_is_rejected(self):
        self.assert_rejected("[click](javascript:alert(1))", "javascript")

    def test_javascript_scheme_autolink_is_rejected(self):
        self.assert_rejected("<javascript:alert(1)>", "javascript")

    def test_uppercase_scheme_does_not_evade_the_check(self):
        base = self.root
        for scheme in ("JavaScript", "JAVASCRIPT", "jAvAsCrIpT"):
            with self.subTest(scheme=scheme):
                self.root = base / scheme
                self.root.mkdir()
                self.assert_rejected(f"[x]({scheme}:alert(1))")

    def test_vbscript_scheme_link_is_rejected(self):
        self.assert_rejected("[x](vbscript:alert(1))", "vbscript")

    def test_data_scheme_link_is_rejected(self):
        self.assert_rejected("[x](data:text/html,alert(1))", "data")

    def test_executable_scheme_inside_a_table_cell_is_rejected(self):
        # mismo nodo Link, posición distinta: el walker del AST no depende de dónde cuelga
        self.assert_rejected("| enlace |\n|---|\n| [x](javascript:alert(1)) |")

    def test_executable_scheme_inside_a_footnote_is_rejected(self):
        self.assert_rejected("ref[^1]\n\n[^1]: nota con [x](javascript:alert(1))")

    def test_http_https_mailto_and_tel_links_are_accepted(self):
        base = self.root
        for i, url in enumerate(("https://example.com", "http://example.com", "mailto:a@example.com", "tel:+123")):
            with self.subTest(url=url):
                self.root = base / str(i)
                self.root.mkdir()
                self.assert_accepted(f"[x]({url})")

    def test_relative_link_is_accepted(self):
        self.assert_accepted("[x](../README.md)")

    def test_anchor_link_is_accepted(self):
        self.assert_accepted("[x](#seccion)")


@unittest.skipUnless(shutil.which("pandoc"), "pandoc no instalado")
class TestMetadataInContentIsRestricted(ConcatenateTestCase):
    """Un bloque YAML a mitad de una sección fusiona metadatos en el documento: sólo los de concatenate.py."""

    def run_with_block(self, block: str) -> subprocess.CompletedProcess:
        self.build()
        write_section(self.m["secciones"], "S01-a.md", f"Antes.\n\n{block}\n\nDespués.\n")
        return run_concat(concat_args(self.m, self.out))

    def test_file_reading_metadata_keys_are_rejected(self):
        keys = ("css", "header-includes", "include-before", "include-after", "include-in-header",
                "bibliography", "csl", "reference-doc", "template")
        for key in keys:
            with self.subTest(key=key):
                self.root = self.root / key
                self.root.mkdir()
                r = self.run_with_block(f"---\n{key}: x\n---")
                self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
                self.assertIn(key, r.stderr)
                self.assertNotIn("Traceback", r.stderr)
                self.assertFalse(self.out.exists())

    def test_a_pair_of_horizontal_rules_around_prose_is_not_metadata(self):
        r = self.run_with_block("---\nuna línea de prosa\n---")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("Después.", self.out.read_text(encoding="utf-8"))

    def test_the_metadata_concatenate_writes_is_accepted(self):
        self.build('---\nnombre_comercial: Acme\nversion: 1.0\nfecha_corte: 2026-10-07\nidioma: en\n---\n')
        write_section(self.m["secciones"], "S01-a.md", "AAA\n")
        self.assertEqual(run_concat(concat_args(self.m, self.out)).returncode, 0)


class TestExitCodes(ConcatenateTestCase):
    def test_missing_arguments_exit_2(self):
        for missing in ("--secciones", "--capturas", "--plan", "--brief", "--output"):
            with self.subTest(missing=missing):
                self.build_fresh()
                args = concat_args(self.m, self.out)
                i = args.index(missing)
                del args[i : i + 2]
                r = run_concat(args)
                self.assertEqual(r.returncode, 2, r.stderr)

    def build_fresh(self):
        shutil.rmtree(self.root / "secciones", ignore_errors=True)
        shutil.rmtree(self.root / "capturas", ignore_errors=True)
        self.build()
        write_section(self.m["secciones"], "S01-a.md", "AAA\n")

    def test_missing_plan_file_exit_2(self):
        self.build_fresh()
        self.m["plan"].unlink()
        r = run_concat(concat_args(self.m, self.out))
        self.assertEqual(r.returncode, 2)
        self.assertIn("faltan plan o brief", r.stderr)

    def test_secciones_not_a_directory_exit_2(self):
        self.build_fresh()
        self.m["secciones"] = self.root / "no-existe"
        r = run_concat(concat_args(self.m, self.out))
        self.assertEqual(r.returncode, 2)

    def test_empty_secciones_exit_2(self):
        self.build()
        r = run_concat(concat_args(self.m, self.out))
        self.assertEqual(r.returncode, 2)
        self.assertIn("no se encontraron secciones", r.stderr)


class TestUntrustedPathsAreRejected(ConcatenateTestCase):
    """Markdown redactado por agentes: ni imágenes ni secciones pueden salir del directorio del manual."""

    def outside_dir(self) -> Path:
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, True)
        return d

    def assert_rejected_image(self, ref: str, fragment: str):
        write_section(self.m["secciones"], "S01-a.md", f"![x]({ref})\n")
        r = run_concat(concat_args(self.m, self.out))
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn(fragment, r.stderr)
        self.assertFalse(self.out.exists(), "se escribió una salida con una imagen no confiable")

    def test_absolute_image_outside_the_manual_is_an_error(self):
        self.build()
        outside = self.outside_dir() / "fuera.png"
        outside.write_bytes(b"x")
        self.assert_rejected_image(str(outside), str(outside))

    def test_relative_image_escaping_the_manual_is_an_error(self):
        self.build()
        outside = self.root.parent / f"{self.root.name}-vecino.png"
        outside.write_bytes(b"x")
        self.addCleanup(outside.unlink)
        self.assert_rejected_image(f"../../{outside.name}", outside.name)

    def test_image_symlinked_out_of_the_manual_is_an_error(self):
        self.build()
        outside = self.outside_dir() / "secreto.png"
        outside.write_bytes(b"x")
        (self.m["capturas"] / "enlace.png").symlink_to(outside)
        self.assert_rejected_image("../capturas/enlace.png", outside.name)

    def test_file_scheme_image_is_an_error(self):
        self.build()
        self.assert_rejected_image("file:///etc/passwd", "file:///etc/passwd")

    def test_absolute_image_inside_the_manual_is_accepted(self):
        # par positivo: la misma configuración con una ruta contenida compila
        self.build()
        inside = (self.m["capturas"] / "login.png").resolve()
        write_section(self.m["secciones"], "S01-a.md", f"![x]({inside})\n")
        self.assertIn(f"![x]({inside})", self.concat())

    def _section_symlink_case(self, indexed: bool):
        self.build()
        write_section(self.m["secciones"], "S01-a.md", "AAA\n")
        external = self.outside_dir() / "ext.md"
        external.write_text("EXTERNO-FUERA\n", encoding="utf-8")
        internal = self.m["secciones"] / "data.txt"  # dentro de secciones/, pero enlazado
        internal.write_text("INTERNO-ENLAZADO\n", encoding="utf-8")
        (self.m["secciones"] / "S02-ext.md").symlink_to(external)
        (self.m["secciones"] / "S03-int.md").symlink_to(internal)
        if indexed:
            write_section(self.m["secciones"], "00-INDICE.md", "- S01-a.md\n- S02-ext.md\n- S03-int.md\n")
        r = run_concat(concat_args(self.m, self.out))
        self.assertEqual(r.returncode, 0, r.stderr)
        text = self.out.read_text(encoding="utf-8")
        self.assertIn("AAA", text)  # el instrumento sigue encendido
        self.assertNotIn("EXTERNO-FUERA", text)
        self.assertNotIn("INTERNO-ENLAZADO", text)
        self.assertIn("S02-ext.md", r.stderr)
        self.assertIn("S03-int.md", r.stderr)

    def test_symlinked_sections_are_omitted_with_index(self):
        self._section_symlink_case(indexed=True)

    def test_symlinked_sections_are_omitted_without_index(self):
        self._section_symlink_case(indexed=False)


class TestImagesValidatedOnPandocAst(ConcatenateTestCase):
    """La contención se valida sobre lo que pandoc resolverá (AST), no sobre la sintaxis `![a](url)`."""

    def outside_file(self, name: str = "fuera.png") -> Path:
        # hermano del manual: alcanzable con `..` desde secciones/
        path = self.root.parent / f"{self.root.name}-{name}"
        path.write_bytes(b"SECRETO")
        self.addCleanup(path.unlink)
        return path

    def assert_rejected(self, content: str, fragment: str | None = None):
        write_section(self.m["secciones"], "S01-a.md", content)
        r = run_concat(concat_args(self.m, self.out))
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        self.assertFalse(self.out.exists(), "se escribió una salida con una imagen no confiable")
        if fragment:
            self.assertIn(fragment, r.stderr)

    def test_reference_style_image_with_absolute_definition_outside_is_rejected(self):
        self.build()
        outside = self.outside_file()
        self.assert_rejected(f"![a][r]\n\n[r]: {outside}\n", str(outside))

    def test_reference_style_image_with_relative_definition_escaping_is_rejected(self):
        self.build()
        outside = self.outside_file()
        self.assert_rejected(f"![a][r]\n\n[r]: ../../{outside.name}\n", outside.name)

    def test_reference_style_image_with_canonical_definition_inside_is_accepted(self):
        # par positivo: la misma sintaxis con una ruta contenida compila
        self.build()
        inside = (self.m["capturas"] / "login.png").resolve()
        write_section(self.m["secciones"], "S01-a.md", f"![a][r]\n\n[r]: {inside}\n")
        self.assertIn(f"[r]: {inside}", self.concat())

    def test_percent_encoded_traversal_is_rejected(self):
        self.build()
        outside = self.outside_file()
        cases = {
            "puntos codificados": f"%2e%2e/%2e%2e/{outside.name}",
            "barra codificada": f"..%2f..%2f{outside.name}",
            "doble codificación": f"%252e%252e/%252e%252e/{outside.name}",
            "mayúsculas": f"%2E%2E/%2E%2E/{outside.name}",
        }
        for label, ref in cases.items():
            with self.subTest(label):
                self.assert_rejected(f"![a]({ref})\n")

    def test_unsupported_scheme_gets_its_own_message(self):
        self.build()
        self.assert_rejected("![a](ftp://h/a.png)\n", "esquema no admitido")

    def test_relative_reference_definition_gets_an_actionable_message(self):
        # las definiciones por referencia no se reescriben: una relativa (aunque sea legítima) se rechaza con guía
        self.build()
        self.assert_rejected("![a][r]\n\n[r]: ../capturas/login.png\n", "ruta relativa sin reescribir")

    def test_reference_definition_with_dotdot_inside_the_manual_is_rejected(self):
        # contenida pero no canónica: pandoc y el SO podrían resolverla distinto a un normalizador léxico
        self.build()
        non_canonical = f"{self.m['capturas'].resolve()}/../capturas/login.png"
        self.assert_rejected(f"![a][r]\n\n[r]: {non_canonical}\n", "no canónica")

    def test_query_or_fragment_traversal_is_rejected(self):
        self.build()
        for ref in (
            "../capturas/login.png?x=/../..", "../capturas/login.png#/../..",
            "../capturas/no.png?/../login.png", "../capturas/no.png#/../login.png",
        ):
            with self.subTest(ref):
                self.assert_rejected(f"![a]({ref})\n")

    def test_nul_in_image_path_is_a_clean_error(self):
        self.build()
        self.assert_rejected("![a](../capturas/lo\x00gin.png)\n")

    def test_nul_in_reference_definition_is_a_clean_error(self):
        self.build()
        self.assert_rejected("![a][r]\n\n[r]: /tmp/lo\x00gin.png\n")

    def test_image_inside_a_table_cell_is_checked(self):
        self.build()
        outside = self.outside_file()
        self.assert_rejected(f"| a |\n|---|\n| ![x]({outside}) |\n", str(outside))

    def test_image_in_brief_metadata_is_checked(self):
        self.build('---\nnombre_comercial: "![x](/etc/passwd)"\nidioma: es\n---\n')
        write_section(self.m["secciones"], "S01-a.md", "AAA\n")
        r = run_concat(concat_args(self.m, self.out))
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("/etc/passwd", r.stderr)

    def test_link_to_a_local_path_is_not_an_image_and_stays_untouched(self):
        # un enlace (no una imagen) a una ruta local sin esquema no se reescribe ni se contiene como las imágenes
        self.build()
        write_section(self.m["secciones"], "S01-a.md", "[l](/etc/passwd)\n")
        text = self.concat()
        self.assertIn("[l](/etc/passwd)", text)

    def test_file_scheme_autolink_is_rejected_by_the_link_scheme_check(self):
        # distinto de la ruta sin esquema de arriba: `file:` SÍ es un esquema, y no está en la lista admitida
        self.build()
        write_section(self.m["secciones"], "S01-a.md", "<file:///etc/hosts>\n")
        r = run_concat(concat_args(self.m, self.out))
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("file", r.stderr)

    @unittest.skipUnless(shutil.which("pandoc"), "pandoc no instalado")
    def test_legit_image_with_percent_encoded_space_still_works(self):
        self.build()
        (self.m["capturas"] / "mi captura.png").write_bytes((self.m["capturas"] / "login.png").read_bytes())
        write_section(self.m["secciones"], "S01-a.md", "![a](../capturas/mi%20captura.png)\n")
        self.concat()
        r = subprocess.run(
            ["pandoc", str(self.out), "-t", "html", "--embed-resources", "--standalone"],
            capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("Could not fetch resource", r.stderr)
        self.assertIn("data:image/png;base64", r.stdout)

    def test_without_pandoc_it_fails_closed_with_a_clear_message(self):
        self.build()
        write_section(self.m["secciones"], "S01-a.md", "AAA\n")
        r = subprocess.run(
            [sys.executable, str(CONCATENATE), *concat_args(self.m, self.out)],
            capture_output=True, text=True, encoding="utf-8", env={"PATH": str(self.root / "vacio")},
        )
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("pandoc", r.stderr)
        self.assertFalse(self.out.exists())


if __name__ == "__main__":
    unittest.main()
