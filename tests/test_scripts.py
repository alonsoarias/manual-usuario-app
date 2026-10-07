"""Tests de compile_pandoc.sh (--to docx) y compile_pdf.sh como procesos reales."""

from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

from fixtures import COMPILE_PANDOC, COMPILE_PDF, CONCATENATE, PANDOC_FROM_FILE, REPO, make_manual, write_section

SYSTEM_BASH = "/bin/bash" if Path("/bin/bash").exists() else "/usr/bin/bash"
BASIC_TOOLS = ("python3", "dirname", "mktemp", "rm", "cat", "mkdir", "tr", "grep", "wc", "awk", "find", "cp", "tee", "date")


def run_script(
    script: Path, args: list[str], path: str | None = None, extra_env: dict | None = None
) -> subprocess.CompletedProcess:
    env = {**os.environ, **(extra_env or {})}
    if path is not None:
        env["PATH"] = path
    return subprocess.run(
        [SYSTEM_BASH, str(script), *args], capture_output=True, text=True, encoding="utf-8", env=env
    )


def script_args(m: dict, output: Path) -> list[str]:
    return [
        "--secciones", str(m["secciones"]),
        "--capturas", str(m["capturas"]),
        "--plan", str(m["plan"]),
        "--brief", str(m["brief"]),
        "--output", str(output),
    ]


def pandoc_args(m: dict, output: Path, to: str = "docx") -> list[str]:
    return [*script_args(m, output), "--to", to]


def args_for(script: Path, m: dict, output: Path) -> list[str]:
    """Argumentos mínimos válidos del script (compile_pandoc.sh exige --to)."""
    return pandoc_args(m, output) if script == COMPILE_PANDOC else script_args(m, output)


class ScriptTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def manual(self, brief: str | None = None) -> dict:
        m = make_manual(self.root, brief)
        write_section(m["secciones"], "S01-intro.md", "# Introducción\n\nHola.\n\n![login](../capturas/login.png)\n")
        write_section(m["secciones"], "00-INDICE.md", "- S01-intro.md\n")
        return m

    def restricted_path(self, tools: tuple[str, ...], stubs: dict[str, str] | None = None) -> str:
        """PATH con sólo los ejecutables pedidos (symlinks) y stubs `sh` {nombre: cuerpo}."""
        bindir = self.root / "bin"
        bindir.mkdir(exist_ok=True)
        for tool in tools:
            real = shutil.which(tool)
            self.assertIsNotNone(real, f"{tool} no está en el PATH del host")
            if not (bindir / tool).exists():
                (bindir / tool).symlink_to(real)
        for name, body in (stubs or {}).items():
            stub = bindir / name
            stub.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
            stub.chmod(0o755)
        return str(bindir)


class TestArguments(ScriptTestCase):
    def test_each_script_without_arguments_exits_2(self):
        for script in (COMPILE_PANDOC, COMPILE_PDF):
            with self.subTest(script=script.name):
                r = run_script(script, [])
                self.assertEqual(r.returncode, 2, r.stderr)

    def test_each_script_missing_one_argument_exits_2(self):
        m = self.manual()
        for script in (COMPILE_PANDOC, COMPILE_PDF):
            for missing in ("--secciones", "--capturas", "--plan", "--brief", "--output"):
                with self.subTest(script=script.name, missing=missing):
                    args = args_for(script, m, self.root / "salida" / "x")
                    i = args.index(missing)
                    del args[i : i + 2]
                    r = run_script(script, args)
                    self.assertEqual(r.returncode, 2, r.stderr)

    def test_each_script_unknown_option_exits_2(self):
        for script in (COMPILE_PANDOC, COMPILE_PDF):
            with self.subTest(script=script.name):
                self.assertEqual(run_script(script, ["--no-existe"]).returncode, 2)

    def test_each_script_help_exits_0(self):
        for script in (COMPILE_PANDOC, COMPILE_PDF):
            with self.subTest(script=script.name):
                r = run_script(script, ["--help"])
                self.assertEqual(r.returncode, 0)
                self.assertIn("Uso:", r.stdout)


class TestMissingTools(ScriptTestCase):
    def test_pdf_without_any_pdf_engine_exits_4(self):
        m = self.manual()
        path = self.restricted_path(("pandoc",) + BASIC_TOOLS)
        r = run_script(COMPILE_PDF, script_args(m, self.root / "salida" / "manual.pdf"), path=path)
        self.assertEqual(r.returncode, 4, r.stdout + r.stderr)
        self.assertIn("no se pudo generar el PDF", r.stderr)

    def test_each_script_without_pandoc_exits_3(self):
        m = self.manual()
        path = self.restricted_path(BASIC_TOOLS)
        for script in (COMPILE_PANDOC, COMPILE_PDF):
            with self.subTest(script=script.name):
                r = run_script(script, args_for(script, m, self.root / "salida" / "x"), path=path)
                self.assertEqual(r.returncode, 3, r.stdout + r.stderr)


@unittest.skipUnless(shutil.which("pandoc"), "pandoc no instalado")
class TestDocx(ScriptTestCase):
    def test_docx_is_a_valid_zip_with_embedded_media(self):
        m = self.manual()
        out = self.root / "salida" / "manual.docx"
        r = run_script(COMPILE_PANDOC, pandoc_args(m, out))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(zipfile.is_zipfile(out))
        with zipfile.ZipFile(out) as z:
            self.assertIsNone(z.testzip())
            names = z.namelist()
        self.assertIn("word/document.xml", names)
        self.assertTrue([n for n in names if n.startswith("word/media/")], names)


    def test_toc_title_and_subtitle_follow_the_brief_language(self):
        m = self.manual("---\nnombre_comercial: Acme\nidioma: en\n---\n")
        out = self.root / "salida" / "manual.docx"
        r = run_script(COMPILE_PANDOC, pandoc_args(m, out))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with zipfile.ZipFile(out) as z:
            xml = z.read("word/document.xml").decode("utf-8")
        self.assertIn("Table of contents", xml)
        self.assertIn("User manual", xml)
        self.assertNotIn("Tabla de contenido", xml)


@unittest.skipUnless(shutil.which("pandoc"), "pandoc no instalado")
class TestDocxUntrustedMarkdown(ScriptTestCase):
    def build_docx(self, content: str, prepare=None, extra_args=()) -> tuple[subprocess.CompletedProcess, Path]:
        m = self.manual()
        if prepare:
            prepare(m)
        write_section(m["secciones"], "S01-intro.md", content)
        out = self.root / "salida" / "manual.docx"
        return run_script(COMPILE_PANDOC, [*pandoc_args(m, out), *extra_args]), out

    def reference_docx(self, *media: str) -> Path:
        """Plantilla del cliente (archivo de confianza) con medios propios en word/media/."""
        ref = self.root / "plantilla.docx"
        with ref.open("wb") as fh:
            subprocess.run(["pandoc", "--print-default-data-file", "reference.docx"], stdout=fh, check=True)
        with zipfile.ZipFile(ref, "a") as z:
            for name in media:
                z.writestr(f"word/media/{name}", b"MEDIO-DE-LA-PLANTILLA")
        return ref

    def read_docx(self, out: Path) -> tuple[str, list[str]]:
        with zipfile.ZipFile(out) as z:
            return z.read("word/document.xml").decode("utf-8"), z.namelist()

    def test_raw_openxml_block_is_not_injected_into_document_xml(self):
        r, out = self.build_docx(
            'Texto VISIBLE-DOCX.\n\n```{=openxml}\n<w:p><w:fldSimple w:instr="INCLUDETEXT /x"/></w:p>\n```\n'
        )
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        xml, _ = self.read_docx(out)
        self.assertIn("VISIBLE-DOCX", xml)  # el instrumento sigue encendido
        self.assertNotIn("<w:fldSimple", xml)

    def test_link_to_a_local_file_is_not_embedded(self):
        secret = self.root / "secreto.txt"
        secret.write_text("CONTENIDO-SECRETO-DOCX", encoding="utf-8")
        r, out = self.build_docx(f"Texto VISIBLE-DOCX [enlace]({secret})\n")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        xml, names = self.read_docx(out)
        self.assertIn("VISIBLE-DOCX", xml)
        self.assertNotIn("CONTENIDO-SECRETO-DOCX", xml)
        self.assertEqual([n for n in names if n.startswith("word/media/")], [])

    def test_reference_style_image_outside_the_manual_is_not_embedded(self):
        secret = self.root.parent / (self.root.name + "-secreto.txt")
        secret.write_text("CONTENIDO-SECRETO-DOCX", encoding="utf-8")
        self.addCleanup(secret.unlink)
        r, out = self.build_docx(f"![a][r]\n\n[r]: {secret}\n")
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertFalse(out.exists())

    def test_math_hidden_image_poc_does_not_embed_outside_files(self):
        # PoC de la ronda 3: `$a`$ ![p](fuera) `b`. Con $..$ como matemática el motor veía la imagen y la
        # validación no. Ahora ambos parsean igual (sin matemática: la «imagen» es texto de un span de código).
        secret = self.root.parent / (self.root.name + "-secret.txt")
        secret.write_text("SECRETCONTENT", encoding="utf-8")
        self.addCleanup(secret.unlink)
        r, out = self.build_docx(f"Mira: $a`$ ![p]({secret}) `b\n")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        xml, names = self.read_docx(out)
        self.assertIn("Mira", xml)  # el instrumento sigue encendido
        self.assertEqual([n for n in names if n.startswith("word/media/")], [])
        self.assertNotIn(b"SECRETCONTENT", out.read_bytes())

    def test_dollar_signs_are_literal_text_in_docx(self):
        # control positivo: contenido legítimo con `$` no se rompe; el costo es que `$..$` sale literal
        content = "Cuesta $5 y $10.\n\n```\necho $HOME\n```\n\n| a | b |\n|---|---|\n| $x$ | 1 |\n"
        r, out = self.build_docx(content)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        xml, _ = self.read_docx(out)
        for literal in ("$5", "$10", "$HOME", "$x$"):
            with self.subTest(literal=literal):
                self.assertIn(literal, xml)

    def test_reference_doc_media_of_vector_formats_is_not_rejected(self):
        # la plantilla del cliente suele traer el logo en .emf/.wmf; pandoc lo copia a word/media/
        ref = self.reference_docx("logo.emf", "marca.wmf")
        r, out = self.build_docx("Texto VISIBLE-DOCX.\n", extra_args=["--reference-doc", str(ref)])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        _, names = self.read_docx(out)
        self.assertIn("word/media/logo.emf", names)  # el instrumento sigue encendido: el medio está en el DOCX

    def test_reference_doc_media_is_trusted_whatever_its_extension(self):
        ref = self.reference_docx("marca.dat")
        r, out = self.build_docx("Texto VISIBLE-DOCX.\n", extra_args=["--reference-doc", str(ref)])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("word/media/marca.dat", self.read_docx(out)[1])

    def test_content_media_is_still_checked_when_a_reference_doc_has_media(self):
        ref = self.reference_docx("logo.emf")

        def prepare(m):
            (m["capturas"] / "nota.txt").write_text("NO-ES-UNA-IMAGEN", encoding="utf-8")

        r, out = self.build_docx("![n](../capturas/nota.txt)\n", prepare, ["--reference-doc", str(ref)])
        self.assertEqual(r.returncode, 7, r.stdout + r.stderr)
        self.assertIn(".txt", r.stderr)  # pandoc renombra el medio añadido a rIdN.txt
        self.assertNotIn("logo.emf", r.stderr)  # sólo se acusa lo añadido por el contenido
        self.assertFalse(out.exists())

    def test_valid_raster_and_document_formats_in_capturas_are_embedded(self):
        for ext in ("bmp", "tif", "tiff", "ico", "eps", "pdf", "emf", "wmf"):
            with self.subTest(ext=ext):
                self.root = self.root / f"caso-{ext}"
                self.root.mkdir()

                def prepare(m, ext=ext):
                    (m["capturas"] / f"figura.{ext}").write_bytes(b"BM" + bytes(64))

                r, out = self.build_docx(f"![f](../capturas/figura.{ext})\n", prepare)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                embedded = "tiff" if ext == "tif" else ext  # pandoc normaliza .tif a .tiff
                self.assertTrue([n for n in self.read_docx(out)[1] if n.endswith(f".{embedded}")], ext)

    def test_non_image_file_embedded_in_word_media_aborts(self):
        # defensa en profundidad: contenida en el manual pero no es una imagen
        def prepare(m):
            (m["capturas"] / "nota.txt").write_text("NO-ES-UNA-IMAGEN", encoding="utf-8")

        r, out = self.build_docx("![n](../capturas/nota.txt)\n", prepare)
        self.assertEqual(r.returncode, 7, r.stdout + r.stderr)
        self.assertIn("no son imágenes", r.stderr)
        self.assertFalse(out.exists())

    def test_legit_image_with_percent_encoded_space_is_embedded(self):
        def prepare(m):
            (m["capturas"] / "mi captura.png").write_bytes((m["capturas"] / "login.png").read_bytes())

        r, out = self.build_docx("![a](../capturas/mi%20captura.png)\n", prepare)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        _, names = self.read_docx(out)
        self.assertTrue([n for n in names if n.startswith("word/media/")], names)


@unittest.skipUnless(shutil.which("typst") and shutil.which("pandoc"), "typst o pandoc no instalado")
class TestTypst(ScriptTestCase):
    def test_pdf_is_built_with_typst(self):
        m = self.manual()
        out = self.root / "salida" / "manual.pdf"
        r = run_script(COMPILE_PDF, script_args(m, out))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("generado con typst", r.stdout)
        pdf = out.read_bytes()
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertIsNotNone(re.search(rb"/Subtype\s*/Image", pdf), "el PDF no embebe la imagen")

    def test_failing_typst_never_downgrades_to_latex(self):
        # Fail-closed: un fallo de Typst provocable desde el contenido no puede abrir la puerta a LaTeX.
        m = self.manual()
        bad_template = self.root / "bad.typ"
        bad_template.write_text("#this-function-does-not-exist(\n", encoding="utf-8")
        out = self.root / "salida" / "manual.pdf"
        ran = self.root / "latex-ran"
        path = self.restricted_path(
            ("pandoc", "typst") + BASIC_TOOLS, stubs={e: f'touch "{ran}"; exit 1' for e in ("xelatex", "pdflatex")}
        )
        r = run_script(
            COMPILE_PDF, script_args(m, out), path=path,
            extra_env={"MANUAL_USUARIO_APP_TYPST_TEMPLATE": str(bad_template)},
        )
        self.assertEqual(r.returncode, 5, r.stdout + r.stderr)
        self.assertIn("no se usa LaTeX", r.stderr)
        self.assertNotIn("Compilando PDF con XeLaTeX", r.stdout)
        self.assertFalse(ran.exists(), "se invocó un motor LaTeX tras el fallo de Typst")
        self.assertFalse(out.exists())


TEMPLATE = REPO / "assets" / "manual-template.typ"


@unittest.skipUnless(shutil.which("typst") and shutil.which("pandoc") and shutil.which("pdftotext"), "typst, pandoc o pdftotext no instalado")
class TestTypstLanguage(ScriptTestCase):
    """El idioma del brief llega a Typst: el título de la tabla de contenido sale traducido."""

    TOC_TITLE = {"es": "Índice", "en": "Contents", "pt": "Sumário"}  # `outline(title: auto)` de Typst 0.15

    def pdf_text(self, lang: str) -> str:
        m = self.manual(f"---\nnombre_comercial: Acme\nidioma: {lang}\n---\n")
        out = self.root / "salida" / "manual.pdf"
        r = run_script(COMPILE_PDF, script_args(m, out))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return subprocess.run(["pdftotext", str(out), "-"], capture_output=True, text=True).stdout

    def test_toc_title_follows_the_brief_language(self):
        base = self.root
        for lang, title in self.TOC_TITLE.items():
            with self.subTest(lang=lang):
                self.root = base / lang
                self.root.mkdir()
                text = self.pdf_text(lang)
                self.assertIn(title, text)
                for other in set(self.TOC_TITLE.values()) - {title}:
                    self.assertNotIn(other, text)

    def test_language_with_region_uses_the_primary_language(self):
        self.assertIn("Sumário", self.pdf_text("pt-BR"))

    def test_template_does_not_break_with_an_invented_or_malformed_lang(self):
        # typst rechaza `klingon`/`es-CO` en text(lang:): la plantilla los normaliza en vez de abortar
        body = TEMPLATE.read_text(encoding="utf-8") + "\n= Uno\nHola\n"
        (self.root / "t.typ").write_text(body, encoding="utf-8")
        for lang in ("klingon", "es-CO", "", "xx"):
            with self.subTest(lang=lang):
                r = subprocess.run(
                    ["typst", "compile", "--root", str(self.root), "--input", f"lang={lang}", str(self.root / "t.typ"), str(self.root / "o.pdf")],
                    capture_output=True, text=True,
                )
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertTrue((self.root / "o.pdf").is_file())

    def test_template_without_lang_input_defaults_to_spanish(self):
        (self.root / "t.typ").write_text(TEMPLATE.read_text(encoding="utf-8") + "\n= Uno\nHola\n", encoding="utf-8")
        r = subprocess.run(["typst", "compile", "--root", str(self.root), str(self.root / "t.typ"), str(self.root / "o.pdf")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Índice", subprocess.run(["pdftotext", str(self.root / "o.pdf"), "-"], capture_output=True, text=True).stdout)


class TestPdfFailureModes(ScriptTestCase):
    FAIL = "exit 1"

    def test_stale_pdf_is_not_reported_as_success_when_every_engine_fails(self):
        m = self.manual()
        out = self.root / "salida" / "manual.pdf"
        out.parent.mkdir()
        out.write_bytes(b"%PDF-1.4 obsoleto")
        path = self.restricted_path(
            ("pandoc",) + BASIC_TOOLS, stubs={"xelatex": self.FAIL, "pdflatex": self.FAIL}
        )
        r = run_script(COMPILE_PDF, script_args(m, out), path=path)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertFalse(out.exists(), "quedó el PDF anterior en la ruta de salida")
        self.assertNotIn("OK — PDF generado", r.stdout)

    def run_with_logging_pandoc(self, fc_list_output: str) -> subprocess.CompletedProcess:
        m = self.manual()
        self.pandoc_log = self.root / "pandoc.log"
        path = self.restricted_path(
            BASIC_TOOLS,
            stubs={
                "pandoc": (
                    # concatenate.py llama a pandoc para validar imágenes: se le contesta con un AST vacío
                    'case "$*" in *"--to json"*) echo \'{"pandoc-api-version":[1,23,1],"meta":{},"blocks":[]}\'; exit 0;; esac; '
                    'echo "CALL $*" >> "$PANDOC_LOG"; exit 1'
                ),
                "xelatex": self.FAIL,
                "pdflatex": self.FAIL,
                "fc-list": 'printf "%s" "$FC_LIST_OUTPUT"',
            },
        )
        return run_script(
            COMPILE_PDF,
            script_args(m, self.root / "salida" / "manual.pdf"),
            path=path,
            extra_env={"PANDOC_LOG": str(self.pandoc_log), "FC_LIST_OUTPUT": fc_list_output},
        )

    def test_xelatex_failure_prints_an_actionable_warning_and_tries_pdflatex(self):
        r = self.run_with_logging_pandoc("DejaVu Sans\n")
        self.assertIn("XeLaTeX falló", r.stderr)
        self.assertIn("babel", r.stderr)
        self.assertIn("fc-list", r.stderr)
        self.assertIn("Compilando PDF con pdfLaTeX", r.stdout)

    def xelatex_call(self) -> str:
        (call,) = [l for l in self.pandoc_log.read_text().splitlines() if "--pdf-engine=xelatex" in l]
        return call

    def test_latex_engines_are_invoked_with_the_shared_from(self):
        self.run_with_logging_pandoc("")
        calls = [l for l in self.pandoc_log.read_text().splitlines() if "--pdf-engine=" in l]
        self.assertEqual(len(calls), 2, calls)  # XeLaTeX y pdfLaTeX
        for call in calls:
            self.assertIn(f"--from={shared_from()} ", call)

    def test_fonts_are_forced_only_when_installed(self):
        cases = {
            "ninguna": ("", False, False),
            "sólo mono (caso de este host)": ("DejaVu Sans Mono\n", False, True),
            "ambas": ("DejaVu Sans,DejaVu Sans Light\nDejaVu Sans Mono\n", True, True),
        }
        base = self.root
        for i, (label, (fc_out, main, mono)) in enumerate(cases.items()):
            with self.subTest(label):
                self.root = base / f"caso{i}"
                self.root.mkdir()
                self.run_with_logging_pandoc(fc_out)
                call = self.xelatex_call()
                self.assertEqual("mainfont=DejaVu Sans" in call, main, call)
                self.assertEqual("monofont=DejaVu Sans Mono" in call, mono, call)


class TestCompilationLog(ScriptTestCase):
    """Ambos scripts escriben salida/compilacion.log con lo que muestran por consola, sin perder su rc."""

    def log(self) -> str:
        return (self.root / "salida" / "compilacion.log").read_text(encoding="utf-8")

    def test_successful_run_writes_the_log(self):
        m = self.manual()
        r = run_script(COMPILE_PANDOC, pandoc_args(m, self.root / "salida" / "manual.docx"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("[1/3] Concatenando", self.log())
        self.assertIn("OK — DOCX generado", self.log())

    def test_log_holds_exactly_what_the_console_shows(self):
        m = self.manual()
        r = run_script(COMPILE_PANDOC, pandoc_args(m, self.root / "salida" / "manual.docx"))
        shown = {l for l in (r.stdout + r.stderr).splitlines() if l.strip()}
        logged = {l for l in self.log().splitlines() if l.strip() and not l.startswith("=== ")}
        self.assertTrue(shown)
        self.assertEqual(logged, shown)

    def test_each_run_appends_a_header_naming_the_script(self):
        m = self.manual()
        out = self.root / "salida" / "manual.docx"
        run_script(COMPILE_PANDOC, pandoc_args(m, out))
        run_script(COMPILE_PANDOC, pandoc_args(m, out, "html"))
        headers = [l for l in self.log().splitlines() if l.startswith("=== ")]
        self.assertEqual(len(headers), 2, headers)
        self.assertTrue(all("compile_pandoc.sh" in h for h in headers), headers)

    def assert_rc_and_log(self, script, args, expected_rc, fragment, path=None):
        r = run_script(script, args, path=path)
        self.assertEqual(r.returncode, expected_rc, r.stdout + r.stderr)
        self.assertIn(fragment, r.stderr)  # sigue llegando a la consola
        self.assertIn(fragment, self.log())

    def test_concatenation_error_keeps_rc_2_and_is_logged(self):
        m = self.manual()
        write_section(m["secciones"], "S01-intro.md", "![x](/etc/hostname)\n")
        for script in (COMPILE_PANDOC, COMPILE_PDF):
            with self.subTest(script=script.name):
                self.assert_rc_and_log(script, args_for(script, m, self.root / "salida" / "x"), 2, "imagen fuera del manual")

    def test_docx_media_error_keeps_rc_7_and_is_logged(self):
        m = self.manual()
        (m["capturas"] / "nota.txt").write_text("NO-ES-UNA-IMAGEN", encoding="utf-8")
        write_section(m["secciones"], "S01-intro.md", "![n](../capturas/nota.txt)\n")
        self.assert_rc_and_log(COMPILE_PANDOC, pandoc_args(m, self.root / "salida" / "manual.docx"), 7, "no son imágenes")

    def test_pdf_without_engines_keeps_rc_4_and_is_logged(self):
        m = self.manual()
        path = self.restricted_path(("pandoc",) + BASIC_TOOLS)
        self.assert_rc_and_log(
            COMPILE_PDF, script_args(m, self.root / "salida" / "manual.pdf"), 4, "no se pudo generar el PDF", path
        )

    def test_pdf_symlink_rejection_keeps_rc_6_and_is_logged(self):
        m = self.manual()
        (m["capturas"] / "enlace.png").symlink_to(self.root)
        self.assert_rc_and_log(COMPILE_PDF, script_args(m, self.root / "salida" / "manual.pdf"), 6, "enlaces simbólicos")


SECRET_DIR_MARK = "SECRETO-FUERA-DEL-MANUAL"
HOSTILE_MD = (
    "Texto VISIBLE-NORMAL.\n\n"
    "\\input{{{secret}}}\n\n"
    "Matemática $\\input{{{secret}}}$ y $$\\input{{{secret}}}$$\n\n"
    "```{{=latex}}\n\\input{{{secret}}}\n```\n"
)


class TestLatexUntrustedMarkdown(ScriptTestCase):
    """El fallback LaTeX recibe Markdown redactado por agentes: no puede ejecutar TeX crudo."""

    def run_capturing_tex(self, engine: str) -> Path:
        m = self.manual()
        secret = self.root / "secreto.txt"
        secret.write_text(SECRET_DIR_MARK, encoding="utf-8")
        write_section(m["secciones"], "S01-intro.md", HOSTILE_MD.format(secret=secret))
        capture = self.root / "capturado.tex"
        # el stub recibe el .tex que pandoc genera con las opciones REALES del script y lo copia
        stub = f'for last; do :; done; cp "$last" "{capture}"; exit 1'
        path = self.restricted_path(("pandoc",) + BASIC_TOOLS, stubs={engine: stub})
        run_script(COMPILE_PDF, script_args(m, self.root / "salida" / "manual.pdf"), path=path)
        self.secret = secret
        return capture

    def assert_no_executable_tex(self, capture: Path):
        self.assertTrue(capture.exists(), "el motor stub no recibió el .tex")
        tex = capture.read_text(encoding="utf-8")
        self.assertIn("VISIBLE-NORMAL", tex)  # el instrumento sigue encendido
        self.assertNotIn("\\input{" + str(self.secret), tex)
        self.assertNotIn("\\(\\input", tex)
        self.assertNotIn("\\[\\input", tex)
        self.assertNotIn("\\input{", tex)

    def test_xelatex_does_not_receive_raw_tex_or_math_from_markdown(self):
        self.assert_no_executable_tex(self.run_capturing_tex("xelatex"))

    def test_pdflatex_does_not_receive_raw_tex_or_math_from_markdown(self):
        self.assert_no_executable_tex(self.run_capturing_tex("pdflatex"))


class TestLegitimateLinksCompileInAllFormats(ScriptTestCase):
    """Control positivo de la validación de esquema de enlaces: lo permitido sigue compilando en los 4 formatos."""

    LINKS = "[sitio](https://example.com) [correo](mailto:a@example.com) [tel](tel:+123) [rel](../README.md) [ancla](#intro)"

    @unittest.skipUnless(shutil.which("pandoc"), "pandoc no instalado")
    def test_http_mailto_tel_relative_and_anchor_links_compile(self):
        base = self.root
        outputs = {"docx": "manual.docx", "html": "manual.html", "gfm": "manual.md", "pdf": "manual.pdf"}
        for to, name in outputs.items():
            with self.subTest(to=to):
                self.root = base / to
                self.root.mkdir()
                m = self.manual()
                write_section(m["secciones"], "S01-intro.md", f"# Intro\n\n{self.LINKS}\n")
                out = self.root / "salida" / name
                if to == "pdf":
                    r = run_script(COMPILE_PDF, script_args(m, out))
                else:
                    r = run_script(COMPILE_PANDOC, pandoc_args(m, out, to))
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                self.assertTrue(out.exists())


class TestSymlinksAreRejected(ScriptTestCase):
    def assert_aborts(self, m: dict):
        out = self.root / "salida" / "manual.pdf"
        r = run_script(COMPILE_PDF, script_args(m, out))
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
        self.assertIn("enlaces simbólicos", r.stderr)
        self.assertFalse(out.exists())
        self.assertNotIn("Compilando PDF", r.stdout)

    def outside_dir(self) -> Path:
        d = self.root.parent / (self.root.name + "-fuera")
        d.mkdir()
        self.addCleanup(shutil.rmtree, d, True)
        return d

    def test_symlink_inside_secciones_aborts(self):
        m = self.manual()
        target = self.outside_dir() / "x.md"
        target.write_text("EXTERNO\n", encoding="utf-8")
        (m["secciones"] / "S02-enlace.md").symlink_to(target)
        self.assert_aborts(m)

    def test_symlink_inside_capturas_aborts(self):
        m = self.manual()
        (m["capturas"] / "enlace.png").symlink_to(self.outside_dir())
        self.assert_aborts(m)

    def test_symlinked_secciones_directory_aborts(self):
        m = self.manual()
        real = self.root / "secciones-real"
        m["secciones"].rename(real)
        m["secciones"].symlink_to(real)
        self.assert_aborts(m)

    def test_regular_manual_is_not_rejected(self):
        # par positivo: sin enlaces la verificación no aborta (llega a la fase de compilación)
        m = self.manual()
        r = run_script(COMPILE_PDF, script_args(m, self.root / "salida" / "manual.pdf"))
        self.assertNotEqual(r.returncode, 6, r.stdout + r.stderr)
        self.assertNotIn("enlaces simbólicos", r.stderr)


@unittest.skipUnless(shutil.which("typst") and shutil.which("pandoc"), "typst o pandoc no instalado")
class TestTypstSandbox(ScriptTestCase):
    """El Markdown lo redactan agentes a partir de la app analizada: no es de confianza."""

    def typst_only_path(self) -> str:
        return self.restricted_path(("pandoc", "typst") + BASIC_TOOLS)

    def compile(self, m: dict) -> tuple[subprocess.CompletedProcess, Path]:
        out = self.root / "salida" / "manual.pdf"
        return run_script(COMPILE_PDF, script_args(m, out), path=self.typst_only_path()), out

    @unittest.skipUnless(shutil.which("pdftotext"), "pdftotext no instalado")
    def test_raw_typst_block_in_markdown_is_not_executed(self):
        m = self.manual()
        secret = self.root / "secreto.txt"  # dentro de la raíz: sólo el bloque raw podría leerlo
        secret.write_text("CONTENIDO-SECRETO", encoding="utf-8")
        write_section(
            m["secciones"], "S01-intro.md",
            f'Texto VISIBLE-NORMAL.\n\n```{{=typst}}\n#read("{secret}")\n```\n',
        )
        r, out = self.compile(m)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        text = subprocess.run(["pdftotext", str(out), "-"], capture_output=True, text=True).stdout
        self.assertIn("VISIBLE-NORMAL", text)  # el instrumento sigue encendido
        self.assertNotIn("CONTENIDO-SECRETO", text)

    def test_image_outside_the_manual_does_not_compile_silently(self):
        m = self.manual()
        with tempfile.TemporaryDirectory() as other:
            outside = Path(other) / "fuera.png"
            outside.write_bytes((m["capturas"] / "login.png").read_bytes())
            write_section(m["secciones"], "S01-intro.md", f"# Intro\n\n![x]({outside})\n")
            r, out = self.compile(m)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertFalse(out.exists())
        # par positivo, misma configuración: la imagen DENTRO del manual sí compila
        write_section(m["secciones"], "S01-intro.md", "# Intro\n\n![x](../capturas/login.png)\n")
        r, out = self.compile(m)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(out.exists())
        self.assertEqual([p.name for p in self.root.glob(".manual-final-*")], [], "quedó el .typ temporal")


    def test_math_hidden_image_poc_does_not_embed_in_typst(self):
        m = self.manual()
        secret = self.root.parent / (self.root.name + "-secret.txt")
        secret.write_text("SECRETCONTENT", encoding="utf-8")
        self.addCleanup(secret.unlink)
        write_section(m["secciones"], "S01-intro.md", f"Mira: $a`$ ![p]({secret}) `b\n")
        r, out = self.compile(m)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIsNone(re.search(rb"/Subtype\s*/Image", out.read_bytes()), "el PDF embebe una imagen")

    @unittest.skipUnless(shutil.which("pdftotext"), "pdftotext no instalado")
    def test_dollar_signs_are_literal_text_in_typst(self):
        m = self.manual()
        write_section(
            m["secciones"], "S01-intro.md",
            "Cuesta $5 y $10.\n\n```\necho $HOME\n```\n\n| a | b |\n|---|---|\n| $x$ | 1 |\n",
        )
        r, out = self.compile(m)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        text = subprocess.run(["pdftotext", str(out), "-"], capture_output=True, text=True).stdout
        for literal in ("$5", "$10", "$HOME", "$x$"):
            with self.subTest(literal=literal):
                self.assertIn(literal, text)

    def test_manual_in_a_directory_with_spaces_and_encoded_image_name_compiles(self):
        # control positivo de la codificación %20 que concatenate.py escribe y pandoc decodifica
        self.root = self.root / "mi manual"
        self.root.mkdir()
        m = self.manual()
        (m["capturas"] / "mi captura.png").write_bytes((m["capturas"] / "login.png").read_bytes())
        write_section(m["secciones"], "S01-intro.md", "# Intro\n\n![x](../capturas/mi%20captura.png)\n")
        r, out = self.compile(m)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIsNotNone(re.search(rb"/Subtype\s*/Image", out.read_bytes()))

    def test_content_triggered_typst_failure_does_not_expose_files_through_latex(self):
        # PoC de la revisión de seguridad: imagen inexistente (Typst falla) + \input{secreto}.
        m = self.manual()
        secret = self.root.parent / (self.root.name + "-secreto.txt")
        secret.write_text(SECRET_DIR_MARK, encoding="utf-8")
        self.addCleanup(secret.unlink)
        write_section(
            m["secciones"], "S01-intro.md",
            f"# Intro\n\n![x](../capturas/no-existe.png)\n\n\\input{{{secret}}}\n",
        )
        ran = self.root / "latex-ran"
        path = self.restricted_path(
            ("pandoc", "typst") + BASIC_TOOLS, stubs={e: f'touch "{ran}"; exit 1' for e in ("xelatex", "pdflatex")}
        )
        out = self.root / "salida" / "manual.pdf"
        r = run_script(COMPILE_PDF, script_args(m, out), path=path)
        self.assertEqual(r.returncode, 5, r.stdout + r.stderr)
        self.assertFalse(ran.exists(), "se invocó LaTeX con el Markdown no confiable")
        self.assertFalse(out.exists())


def shared_from() -> str:
    """El `--from` común, de su única fuente de verdad (un archivo que leen Python y los scripts)."""
    assert PANDOC_FROM_FILE.exists(), f"falta {PANDOC_FROM_FILE}"
    return PANDOC_FROM_FILE.read_text(encoding="utf-8").strip()


class TestOneSourceOfTruthForPandocFrom(unittest.TestCase):
    """Clase de defecto: la validación y cada motor deben parsear el Markdown con las MISMAS extensiones."""

    def test_the_shared_value_is_the_restrictive_one(self):
        self.assertEqual(shared_from(), "markdown-raw_tex-raw_attribute-tex_math_dollars-raw_html-native_divs-native_spans-bracketed_spans-fenced_divs-link_attributes-header_attributes-fenced_code_attributes-inline_code_attributes")

    def test_every_pandoc_from_in_the_shell_scripts_is_the_shared_variable(self):
        expected = {COMPILE_PANDOC: 1, COMPILE_PDF: 3}  # DOCX; Typst, XeLaTeX y pdfLaTeX
        for script, count in expected.items():
            with self.subTest(script=script.name):
                found = re.findall(r'--from=("[^"]*"|\S+)', script.read_text(encoding="utf-8"))
                self.assertEqual(found, ['"$PANDOC_FROM"'] * count)

    def test_shell_scripts_read_the_shared_file(self):
        for script in (COMPILE_PANDOC, COMPILE_PDF):
            with self.subTest(script=script.name):
                self.assertIn('PANDOC_FROM="$(<"$SCRIPT_DIR/pandoc-from.txt")"', script.read_text(encoding="utf-8"))

    def test_concatenate_validates_with_the_shared_value(self):
        spec = importlib.util.spec_from_file_location("concatenate_under_test", CONCATENATE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.PANDOC_FROM, shared_from())

    def test_every_pandoc_command_in_the_skill_uses_the_shared_value(self):
        skill = (REPO / "skills" / "manual-compiler" / "SKILL.md").read_text(encoding="utf-8")
        # DOCX, HTML, GFM, Typst, XeLaTeX, pdfLaTeX
        self.assertEqual(re.findall(r"pandoc --from=(\S+)", skill), [shared_from()] * 6)


class TestSkillDocumentsTheScripts(unittest.TestCase):
    """Los comandos pandoc y los códigos de salida del SKILL salen de los scripts, no de memoria."""

    @classmethod
    def setUpClass(cls):
        cls.skill = (REPO / "skills" / "manual-compiler" / "SKILL.md").read_text(encoding="utf-8")
        cls.pdf = COMPILE_PDF.read_text(encoding="utf-8")
        cls.docx = COMPILE_PANDOC.read_text(encoding="utf-8")

    def test_every_image_extension_the_docx_check_accepts_is_documented(self):
        (block,) = re.findall(r"IMAGE_EXTENSIONS = \{(.*?)\}", self.docx, re.DOTALL)
        extensions = re.findall(r'"([a-z]+)"', block)
        self.assertGreaterEqual(len(extensions), 14, extensions)
        section = self.skill[self.skill.index("**Qué cuenta como imagen (rc 7):**"):]
        section = section[:section.index("\n- ")]
        for ext in extensions:
            with self.subTest(ext=ext):
                self.assertRegex(section, rf"\b{ext}\b")

    def test_every_exit_code_of_the_scripts_is_in_the_skill_table(self):
        codes = {int(c) for text in (self.pdf, self.docx) for c in re.findall(r"^\s*exit (\d)$", text, re.MULTILINE)}
        self.assertTrue({2, 3, 4, 5, 6} <= codes, codes)
        table = self.skill[self.skill.index("## Seguridad y códigos de salida"):]
        for code in sorted(codes - {0}):
            with self.subTest(code=code):
                self.assertRegex(table, rf"(?m)^\| {code} \|", msg=f"rc {code} sin documentar")


def repo_text_files():
    skip = {".git", "__pycache__"}
    for path in sorted(REPO.rglob("*")):
        if path.is_file() and not skip & set(path.relative_to(REPO).parts) and path.suffix in {".md", ".sh", ".py", ".typ", ".json"}:
            yield path


class TestDocsMatchTheScripts(unittest.TestCase):
    """Lo que los SKILL y comandos prometen es lo que los scripts hacen."""

    @classmethod
    def setUpClass(cls):
        cls.compiler = (REPO / "skills" / "manual-compiler" / "SKILL.md").read_text(encoding="utf-8")
        cls.command = (REPO / "commands" / "manual-compile.md").read_text(encoding="utf-8")
        cls.script = COMPILE_PANDOC.read_text(encoding="utf-8")

    def test_the_old_script_name_is_gone_everywhere(self):
        old = "compile_" + "docx"
        self.assertEqual([str(p.relative_to(REPO)) for p in repo_text_files() if old in p.read_text(encoding="utf-8")], [])

    def test_skill_and_command_document_every_format_of_compile_pandoc(self):
        formats = re.search(r"^\s+(docx(?:\|\w+)+)\)\s*;;", self.script, re.MULTILINE).group(1)
        for fmt in formats.split("|"):
            with self.subTest(fmt=fmt):
                self.assertIn(f"--to {fmt}", self.compiler)
                self.assertIn(f"--to {fmt}", self.command)

    def test_compile_stage_defers_the_page_tolerance_to_the_verifier(self):
        # el ±20% antiguo contradecía el ±40% del verificador; la tolerancia vive sólo en manual-verifier
        for path in [*(REPO / "commands").glob("*.md"), *(REPO / "skills").rglob("*.md")]:
            with self.subTest(file=str(path.relative_to(REPO))):
                self.assertNotIn("±20", path.read_text(encoding="utf-8"))
        self.assertEqual(re.findall(r"±\s*\d+\s*%", self.compiler), [])
        self.assertEqual(re.findall(r"±\s*\d+\s*%", self.command), [])
        verifier = (REPO / "skills" / "manual-verifier" / "SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"±\s*\d+\s*%", verifier), ["±40%"])
        self.assertIn("manual-verifier", self.compiler)  # el compilador remite al verificador
        self.assertIn("manual-verify", self.command)

    def test_compiler_skill_promises_only_what_the_scripts_do(self):
        self.assertNotRegex(self.compiler, r"(?i)inserta\s+marcas")
        self.assertIn("compilacion.log", self.compiler)
        for script in (COMPILE_PANDOC, COMPILE_PDF):
            self.assertIn("compilacion.log", script.read_text(encoding="utf-8"))

    def test_brief_template_documents_the_web_formats(self):
        brainstormer = (REPO / "skills" / "manual-brainstormer" / "SKILL.md").read_text(encoding="utf-8")
        block = brainstormer[brainstormer.index("\nformato:\n"):]
        block = block[: block.index("\n\n")]
        for key in ("docx", "pdf", "html", "markdown"):
            self.assertRegex(block, rf"(?m)^  {key}: true \| false", key)
        self.assertIn("formato.html", self.command)
        self.assertIn("formato.markdown", self.command)


if __name__ == "__main__":
    unittest.main()
