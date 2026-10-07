"""Tests de las salidas web de compile_pandoc.sh (--to html|gfm) y de sus defensas.

El Markdown de secciones/ lo redactan agentes a partir de una app de terceros: no es de confianza.
"""

from __future__ import annotations

import http.server
import os
import re
import shutil
import subprocess
import sys
import threading
import unittest
from pathlib import Path

from fixtures import CHECK_WEB_OUTPUT, COMPILE_PANDOC, write_section
from test_scripts import ScriptTestCase, pandoc_args, run_script, script_args

SECRET = "SECRETO-FUERA-DEL-MANUAL"
CSS_SECRET = "CSS-SECRETO-REAL"
CSS_TEXT = f"body{{color:red}}.l::after{{content:'{CSS_SECRET}'}}"


class HitServer:
    """Servidor HTTP local que cuenta las peticiones: prueba que el compilador no sale a la red."""

    def __init__(self, png: bytes):
        hits: list[str] = []
        self.hits = hits

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802 (API de http.server)
                hits.append(self.path)
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.end_headers()
                self.wfile.write(png)

            def log_message(self, *args):
                pass

        self.httpd = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


@unittest.skipUnless(shutil.which("pandoc"), "pandoc no instalado")
class WebTestCase(ScriptTestCase):
    def build(self, to: str, content: str | None = None, prepare=None) -> tuple:
        m = self.manual()
        if prepare:
            prepare(m)
        if content is not None:
            write_section(m["secciones"], "S01-intro.md", content)
        out = self.root / "salida" / ("manual.html" if to == "html" else "manual.md")
        r = run_script(COMPILE_PANDOC, pandoc_args(m, out, to))
        return r, out, m

    def assert_passes_web_check(self, out: Path):
        env = {**os.environ, "HOME": str(Path.home())}  # el HOME real: la salida no debe llevar el directorio de quien compila
        r = subprocess.run([sys.executable, str(CHECK_WEB_OUTPUT), str(out)], capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def outside(self, name: str, data: bytes | str) -> Path:
        """Archivo hermano del manual: alcanzable con rutas absolutas o `..`."""
        path = self.root.parent / f"{self.root.name}-{name}"
        path.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
        self.addCleanup(path.unlink)
        return path


class TestToOption(ScriptTestCase):
    def test_missing_or_unknown_format_exits_2(self):
        m = self.manual()
        out = self.root / "salida" / "x"
        for label, extra in (("sin --to", []), ("pdf", ["--to", "pdf"]), ("vacío", ["--to", ""]), ("epub", ["--to", "epub"])):
            with self.subTest(label):
                r = run_script(COMPILE_PANDOC, [*script_args(m, out), *extra])
                self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
                self.assertFalse(out.exists())

    def test_help_documents_the_three_formats(self):
        r = run_script(COMPILE_PANDOC, ["--help"])
        self.assertEqual(r.returncode, 0)
        for fmt in ("docx", "html", "gfm"):
            self.assertIn(fmt, r.stdout)


class TestHtml(WebTestCase):
    def test_html_is_standalone_with_the_image_embedded(self):
        r, out, _ = self.build("html")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        html = out.read_text(encoding="utf-8")
        self.assertIn("Hola.", html)
        self.assertEqual(len(re.findall(r'<img [^>]*src="data:image/png;base64,', html)), 1, html[:400])
        self.assertNotIn("file:", html)
        self.assertNotIn(str(self.root), html)
        self.assert_passes_web_check(out)

    def test_stale_output_is_removed_when_compilation_fails(self):
        m = self.manual()
        out = self.root / "salida" / "manual.html"
        out.parent.mkdir()
        out.write_text("<html>obsoleto</html>", encoding="utf-8")
        write_section(m["secciones"], "S01-intro.md", "![x](/etc/hostname)\n")
        r = run_script(COMPILE_PANDOC, pandoc_args(m, out, "html"))
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertFalse(out.exists(), "quedó la salida anterior tras un fallo")


class TestGfm(WebTestCase):
    def test_gfm_writes_markdown_with_relative_media(self):
        r, out, _ = self.build("gfm")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        md = out.read_text(encoding="utf-8")
        refs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", md)
        self.assertEqual(len(refs), 1, md)
        self.assertTrue(refs[0].startswith("web/"), refs[0])
        self.assertTrue((out.parent / refs[0]).is_file(), f"{refs[0]} no existe junto a {out}")
        self.assertNotIn(str(self.root), md)
        self.assertNotIn("/home/", md)
        self.assert_passes_web_check(out)

    def test_gfm_media_stay_inside_the_output_directory(self):
        r, out, _ = self.build("gfm")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(sorted(p.name for p in out.parent.iterdir()), ["compilacion.log", "manual.md", "web"])
        self.assertEqual([p.suffix for p in (out.parent / "web").iterdir()], [".png"])


# {png}/{txt}/{css}: archivos FUERA del manual (ruta absoluta); login.png/x.css/x.txt: dentro, alcanzables por
# --resource-path; {url}: servidor local que cuenta peticiones.
HOSTILE_VECTORS = {
    "img_absolute_outside": '<img src="{png}">',
    "img_relative_inside_resource_path": '<img src="login.png">',
    "iframe_file_scheme": '<iframe src="file://{txt}"></iframe>',
    "iframe_absolute": '<iframe src="{txt}"></iframe>',
    "link_stylesheet_absolute": '<link rel="stylesheet" href="{css}">',
    "link_stylesheet_relative": '<link rel="stylesheet" href="x.css">',
    "script_src": '<script src="{txt}"></script>',
    "script_src_relative": '<script src="x.txt"></script>',
    "style_import": '<style>@import url("{css}");</style>',
    "svg_image": '<svg xmlns="http://www.w3.org/2000/svg"><image href="{png}"/></svg>',
    "object_data": '<object data="{txt}"></object>',
    "video_src_and_poster": '<video src="{txt}" poster="{png}"></video>',
    "style_attribute_url": '<p style="background:url({png})">x</p>',
    "div_style_attribute_url": '<div style="background:url({png})">x</div>',
    "remote_img": '<img src="{url}/raw-img.png">',
    "remote_script": '<script src="{url}/raw.js"></script>',
    "remote_stylesheet": '<link rel="stylesheet" href="{url}/raw.css">',
    "remote_iframe": '<iframe src="{url}/raw.html"></iframe>',
}


ATTRIBUTE_INJECTION_VECTORS = {
    # Vectores que NO pasan por raw_html: pandoc los parsea como nodos nativos con atributos crudos
    # (div/span, encabezados, enlaces, imágenes, código) y los re-emite con esos atributos intactos.
    "html_div_with_event_handler": '<div onmouseover="alert(document.cookie)">clickme</div>',
    "bracketed_span_with_event_handler": '[x]{onclick="alert(1)"}',
    "fenced_div_with_event_handler": '::: {onmouseover="alert(1)"}\ncontenido\n:::',
    "header_attribute_event_handler": '# Titulo {onmouseover="alert(1)"}',
    "link_attribute_event_handler": '[enlace](https://example.com){onclick="alert(1)"}',
    "image_attribute_event_handler": '![a](../capturas/login.png){onerror="alert(1)"}',
    "inline_code_attribute_event_handler": '`codigo`{onmouseover="alert(1)"}',
    "fenced_code_attribute_event_handler": '```{.python onmouseover="alert(1)"}\nprint(1)\n```',
}

LIVE_ATTRIBUTE_RE = re.compile(r"<[a-zA-Z][^>]*\son\w+\s*=", re.IGNORECASE)


class TestAttributeInjectionIsNeverLive(WebTestCase):
    """Nodos nativos (div/span/encabezado/enlace/imagen/código) conservan atributos crudos sin pasar por raw_html."""

    def run_vector(self, to: str, name: str) -> tuple:
        m = self.manual()
        write_section(
            m["secciones"], "S01-intro.md",
            f"# Intro\n\nTexto VISIBLE.\n\n{ATTRIBUTE_INJECTION_VECTORS[name]}\n",
        )
        out = self.root / "salida" / ("manual.html" if to == "html" else "manual.md")
        return run_script(COMPILE_PANDOC, pandoc_args(m, out, to)), out

    def test_html_never_carries_a_live_event_handler_attribute(self):
        for name in ATTRIBUTE_INJECTION_VECTORS:
            with self.subTest(vector=name):
                self.root = self.root / name
                self.root.mkdir()
                r, out = self.run_vector("html", name)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                html = out.read_text(encoding="utf-8")
                self.assertIn("VISIBLE", html)  # el instrumento sigue encendido
                self.assertIsNone(LIVE_ATTRIBUTE_RE.search(html), html)

    def test_docx_never_carries_a_live_event_handler_attribute(self):
        # negativo-de-control: docx no ejecuta atributos, pero tampoco debe perder el texto visible
        for name in ATTRIBUTE_INJECTION_VECTORS:
            with self.subTest(vector=name):
                self.root = self.root / name
                self.root.mkdir()
                r, out = self.run_vector("docx", name)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class TestRawHtmlIsNeverResolved(WebTestCase):
    """`--embed-resources` incrusta/descarga lo que el HTML crudo referencia: el HTML crudo no debe llegar a pandoc."""

    def setUp(self):
        super().setUp()
        self.server = HitServer(b"\x89PNG\r\n\x1a\n")
        self.addCleanup(self.server.close)

    def run_vector(self, to: str, name: str):
        m = self.manual()
        (m["root"] / "x.css").write_text(CSS_TEXT, encoding="utf-8")
        (m["root"] / "x.txt").write_text(SECRET, encoding="utf-8")
        png = self.outside("fuera.png", (m["capturas"] / "login.png").read_bytes())
        txt = self.outside("secreto.txt", SECRET)
        css = self.outside("fuera.css", CSS_TEXT)
        snippet = HOSTILE_VECTORS[name].format(png=png, txt=txt, css=css, url=self.server.url)
        write_section(
            m["secciones"], "S01-intro.md",
            f"# Intro\n\nTexto VISIBLE.\n\n![login](../capturas/login.png)\n\n{snippet}\n",
        )
        out = self.root / "salida" / ("manual.html" if to == "html" else "manual.md")
        return run_script(COMPILE_PANDOC, pandoc_args(m, out, to)), out

    def test_html_embeds_only_the_validated_image(self):
        for name in HOSTILE_VECTORS:
            with self.subTest(vector=name):
                self.root = self.root / name
                self.root.mkdir()
                r, out = self.run_vector("html", name)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                html = out.read_text(encoding="utf-8")
                self.assertIn("VISIBLE", html)  # el instrumento sigue encendido
                self.assertEqual(html.count("data:"), 1, "se incrustó algo más que la imagen validada")
                self.assertNotIn(SECRET, html)
                self.assertNotIn(CSS_SECRET, html)
                self.assertEqual(self.server.hits, [], "el compilador hizo una petición de red")

    def test_gfm_copies_only_the_validated_image(self):
        for name in HOSTILE_VECTORS:
            with self.subTest(vector=name):
                self.root = self.root / name
                self.root.mkdir()
                r, out = self.run_vector("gfm", name)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                md = out.read_text(encoding="utf-8")
                self.assertIn("VISIBLE", md)
                self.assertEqual(len(list((out.parent / "web").iterdir())), 1, "se copió algo más que la imagen validada")
                self.assertNotIn(SECRET, md)
                self.assertEqual(self.server.hits, [], "el compilador hizo una petición de red")

    def test_remote_markdown_image_is_rejected_before_any_request(self):
        for to in ("html", "docx", "gfm"):
            with self.subTest(to=to):
                self.root = self.root / to
                self.root.mkdir()
                m = self.manual()
                write_section(m["secciones"], "S01-intro.md", f"Texto VISIBLE.\n\n![x]({self.server.url}/md.png)\n")
                out = self.root / "salida" / "manual.out"
                r = run_script(COMPILE_PANDOC, pandoc_args(m, out, to))
                self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
                self.assertIn("imagen remota", r.stderr)
                self.assertFalse(out.exists())
                self.assertEqual(self.server.hits, [])

    def test_stylesheet_from_a_metadata_block_in_the_content_is_rejected(self):
        # PoC: un bloque YAML a mitad del documento con `css:`; pandoc lo emite como <link> y --embed-resources lo incrusta
        m = self.manual()
        (m["root"] / "x.css").write_text(CSS_TEXT, encoding="utf-8")
        write_section(m["secciones"], "S01-intro.md", "Texto VISIBLE.\n\n---\ncss: x.css\n---\n\nfin\n")
        out = self.root / "salida" / "manual.html"
        r = run_script(COMPILE_PANDOC, pandoc_args(m, out, "html"))
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("css", r.stderr)
        self.assertFalse(out.exists())
