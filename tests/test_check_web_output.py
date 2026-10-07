"""Tests de manual-verifier/scripts/check_web_output.py (script standalone, sin gate automático todavía)."""

from __future__ import annotations

import base64
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from fixtures import CHECK_WEB_OUTPUT, png_bytes

PNG_URI = "data:image/png;base64," + base64.b64encode(png_bytes()).decode()


def page(body: str) -> str:
    return f"<!DOCTYPE html><html><head><title>t</title></head><body>{body}</body></html>"


class CheckerTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def check(self, *args, home: str | None = None) -> subprocess.CompletedProcess:
        env = {**os.environ, "HOME": home or str(self.root / "no-home")}
        return subprocess.run(
            [sys.executable, str(CHECK_WEB_OUTPUT), *map(str, args)],
            capture_output=True, text=True, encoding="utf-8", env=env,
        )

    def write(self, name: str, content: str) -> Path:
        path = self.root / name
        path.write_text(content, encoding="utf-8")
        return path

    def assert_clean(self, path: Path):
        r = self.check(path)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def assert_violation(self, path: Path, fragment: str, **kwargs):
        r = self.check(path, **kwargs)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn(fragment, r.stdout)
        self.assertIn(path.name, r.stdout)  # el informe nombra el archivo


class TestHtmlOutput(CheckerTestCase):
    def test_self_contained_page_passes(self):
        self.assert_clean(self.write("m.html", page(f'<p>Hola</p><img src="{PNG_URI}" alt="a">')))

    def test_relative_image_that_exists_passes(self):
        (self.root / "login.png").write_bytes(png_bytes())
        self.assert_clean(self.write("m.html", page('<img src="login.png">')))

    def test_relative_image_that_does_not_exist_fails(self):
        self.assert_violation(self.write("m.html", page('<img src="falta.png">')), "falta.png")

    def test_local_paths_and_schemes_in_attributes_fail(self):
        cases = {
            "file_scheme": ('<img src="file:///tmp/x.png">', "file:"),
            "absolute_path": ('<img src="/srv/capturas/x.png">', "ruta absoluta local (/srv/capturas/x.png)"),
            "windows_path": ('<img src="C:\\Users\\ana\\x.png">', "C:\\Users"),
            "remote_image": ('<img src="https://example.com/x.png">', "recurso remoto, no autocontenido (https://example.com/x.png)"),
            "protocol_relative": ('<img src="//example.com/x.png">', "recurso remoto, no autocontenido (//example.com/x.png)"),
        }
        for label, (body, fragment) in cases.items():
            with self.subTest(label):
                self.assert_violation(self.write(f"{label}.html", page(body)), fragment)

    def test_active_content_fails(self):
        cases = {
            "script": "<script>alert(1)</script>",
            "iframe": '<iframe src="data:text/html,x"></iframe>',
            "object": '<object data="data:text/plain,x"></object>',
            "embed": '<embed src="data:text/plain,x">',
            "handler": f'<img src="{PNG_URI}" onerror="alert(1)">',
            "javascript_href": '<a href="javascript:alert(1)">x</a>',
        }
        for label, body in cases.items():
            with self.subTest(label):
                r = self.check(self.write(f"{label}.html", page(body)))
                self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_stylesheet_link_to_a_local_file_fails(self):
        self.assert_violation(
            self.write("m.html", '<html><head><link rel="stylesheet" href="/home/ana/x.css"></head></html>'), "/home/ana/x.css"
        )

    def test_file_urls_and_user_paths_in_text_or_css_fail(self):
        cases = {
            "css_url": "<style>p{background:url(file:///etc/x.png)}</style>",
            "file_url_in_text": "<p>Abre file:///etc/passwd</p>",
            "home_dir": "<p>Generado en /home/ana/proyectos/manual</p>",
            "users_dir": "<p>/Users/ana/Documents</p>",
            "user_home_from_env": f"<p>{self.root}/no-home/manual</p>",
        }
        for label, body in cases.items():
            with self.subTest(label):
                r = self.check(self.write(f"{label}.html", page(body)))
                self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_css_urls_are_checked_in_style_blocks_and_attributes(self):
        cases = {
            "block_remote": "<style>p{background:url(https://example.com/x.png)}</style>",
            "block_absolute": "<style>p{background:url('/srv/x.png')}</style>",
            "attribute_absolute": '<p style="background:url(/srv/x.png)">x</p>',
            "attribute_missing_relative": '<p style="background:url(falta.png)">x</p>',
        }
        for label, body in cases.items():
            with self.subTest(label):
                self.assert_violation(self.write(f"{label}.html", page(body)), "url() en CSS")
        self.assert_clean(self.write("ok.html", page(f"<style>p{{background:url({PNG_URI})}}</style>")))

    def test_all_violations_are_reported_not_just_the_first(self):
        path = self.write("m.html", page('<img src="file:///a.png"><img src="/b.png"><script></script>'))
        r = self.check(path)
        self.assertEqual(r.returncode, 1)
        self.assertGreaterEqual(len([l for l in r.stdout.splitlines() if l.startswith("ERROR")]), 3, r.stdout)


class TestMarkdownOutput(CheckerTestCase):
    def test_relative_image_that_exists_passes(self):
        (self.root / "web").mkdir()
        (self.root / "web" / "a.png").write_bytes(png_bytes())
        self.assert_clean(self.write("m.md", "# T\n\n![a](web/a.png)\n"))

    def test_relative_image_is_resolved_from_the_markdown_file_not_the_cwd(self):
        (self.root / "web").mkdir()
        (self.root / "web" / "a.png").write_bytes(png_bytes())
        md = self.write("m.md", "![a](web/a.png)\n")
        r = subprocess.run(
            [sys.executable, str(CHECK_WEB_OUTPUT), str(md)], capture_output=True, text=True, cwd="/", env={**os.environ, "HOME": "/nonexistent-home"}
        )
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_image_references_that_do_not_resolve_or_leak_fail(self):
        cases = {
            "missing": ("![a](web/falta.png)", "web/falta.png"),
            "absolute": ("![a](/srv/x.png)", "/srv/x.png"),
            "file_scheme": ("![a](file:///tmp/x.png)", "file:"),
            "remote": ("![a](https://example.com/x.png)", "https://example.com/x.png"),
            "html_img": ('<img src="/srv/x.png">', "/srv/x.png"),
            "encoded_space_missing": ("![a](web/mi%20captura.png)", "mi%20captura.png"),
            "home_in_text": ("Ruta /home/ana/manual", "/home/ana"),
        }
        for label, (body, fragment) in cases.items():
            with self.subTest(label):
                self.assert_violation(self.write(f"{label}.md", body + "\n"), fragment)

    def test_percent_encoded_image_name_resolves_to_the_decoded_file(self):
        (self.root / "web").mkdir()
        (self.root / "web" / "mi captura.png").write_bytes(png_bytes())
        self.assert_clean(self.write("m.md", "![a](web/mi%20captura.png)\n"))

    def test_image_escaping_the_output_directory_fails(self):
        out = self.root / "salida"
        out.mkdir()
        (self.root / "fuera.png").write_bytes(png_bytes())
        (out / "m.md").write_text("![a](../fuera.png)\n", encoding="utf-8")
        r = self.check(out / "m.md")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("fuera.png", r.stdout)


class TestUsage(CheckerTestCase):
    def test_no_arguments_is_a_usage_error(self):
        self.assertEqual(self.check().returncode, 2)

    def test_missing_file_is_a_usage_error(self):
        r = self.check(self.root / "no-existe.html")
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("no-existe.html", r.stderr)

    def test_unsupported_extension_is_a_usage_error(self):
        self.assertEqual(self.check(self.write("m.txt", "x")).returncode, 2)

    def test_directory_checks_its_html_and_markdown_files(self):
        self.write("manual.html", page("<p>ok</p>"))
        self.write("manual.md", "texto\n")
        self.assert_clean(self.root)
        self.write("otro.html", page('<img src="/srv/x.png">'))
        r = self.check(self.root)
        self.assertEqual(r.returncode, 1)
        self.assertIn("otro.html", r.stdout)

    def test_directory_without_web_outputs_is_a_usage_error(self):
        self.write("compilacion.log", "x")
        self.assertEqual(self.check(self.root).returncode, 2)
