"""Tests del script de enmascarado de screenshot-capturer/references/pii-masking.md, ejecutado en un Chrome real.

El script es la única fuente (Playwright MCP y Chrome DevTools MCP lo reusan): se extrae del .md tal cual y se
corre en headless Chrome sobre una página con datos personales; se lee lo que la captura vería.
"""

from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from fixtures import PII_MASKING_MD, PII_NEGATIVES, PII_POSITIVES, REPO

CHROME = next((shutil.which(c) for c in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser") if shutil.which(c)), None)
SCRIPT_MARK = "<!-- pii-mask:script -->"
AVATAR_PNG = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC"

# Lo que la captura muestra: texto renderizado, valores de campos, atributos visibles e imágenes.
COLLECT = """
const out = {
  text: document.body.innerText,
  values: [...document.querySelectorAll('input, textarea')].map(e => e.value),
  attrs: [...document.querySelectorAll('*')].flatMap(e => ['alt', 'title', 'aria-label', 'placeholder', 'href'].map(a => e.getAttribute(a) || '')),
  images: [...document.querySelectorAll('img')].map(e => e.src),
  backgrounds: [...document.querySelectorAll('*')].map(e => getComputedStyle(e).backgroundImage),
  result: window.__result,
};
const pre = document.createElement('pre');
pre.id = '__out';
pre.textContent = JSON.stringify(out);
document.body.appendChild(pre);
"""


def masking_script(md: Path = PII_MASKING_MD, mark: str = SCRIPT_MARK) -> str:
    """El bloque ```js que sigue a la marca `mark`: el que se pega en browser_evaluate / evaluate_script."""
    text = md.read_text(encoding="utf-8")
    m = re.search(re.escape(mark) + r"\s*```js\n(.*?)\n```", text, re.S)
    if not m:
        raise AssertionError(f"{md} no tiene un bloque ```js tras {mark}")
    return m.group(1)


def run_in_chrome(script: str, body: str) -> dict:
    """Carga `body`, ejecuta `script` (una función) como lo haría el MCP y devuelve lo que vería la captura."""
    page = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>"
        f"{body}<script>window.__result = ({script})();\n{COLLECT}</script></body></html>"
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "page.html"
        path.write_text(page, encoding="utf-8")
        r = subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--no-first-run",
             f"--user-data-dir={tmp}/profile", "--dump-dom", path.as_uri()],
            capture_output=True, text=True, timeout=120,
        )
    m = re.search(r'<pre id="__out">(.*?)</pre>', r.stdout, re.S)
    if not m:
        raise AssertionError(f"Chrome no ejecutó el script (rc={r.returncode}):\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
    return json.loads(html.unescape(m.group(1)))


def visible(seen: dict) -> str:
    return "\n".join([seen["text"], *seen["values"], *seen["attrs"]])


ADMIN_PAGE = f"""
<h2>Bienvenido, Ana María Pérez</h2>
<header><span class="user-name">Ana María Pérez</span>
  <img class="avatar" src="{AVATAR_PNG}" alt="Foto de Ana María Pérez" width="40" height="40"></header>
<div class="profile-photo" style="width:40px;height:40px;background-image:url('{AVATAR_PNG}')"></div>
<table>
  <tr><td>luis.gomez@cliente.co <b>(admin)</b></td></tr>
  <tr><td>eva@cliente.co</td><td>+57 300 123 4567</td></tr>
</table>
<p>Contacto: ana.perez@gmail.com</p>
<form><input name="email" value="marta.ruiz@empresa.com"><textarea>Llamar al 300 123 4568</textarea>
  <select name="usuario"><option value="">Seleccione...</option><option value="7">Pedro Díaz Rojas</option></select>
  <select name="rol"><option value="e">Editor</option><option value="a">Administrador</option></select></form>
<a href="mailto:jorge@cliente.co" title="jorge@cliente.co">Escribir al responsable</a>
"""


@unittest.skipUnless(CHROME, "sin Chrome/Chromium headless")
class TestMaskingScript(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        corpus = "".join(f"<p>{html.escape(text)}</p>" for _, text, _ in PII_POSITIVES)
        corpus += "".join(f'<p class="neg">{html.escape(text)}</p>' for text in PII_NEGATIVES)
        cls.corpus = run_in_chrome(masking_script(), corpus)
        # Como indica el procedimiento: el capturador rellena NOMBRES_REALES con los nombres que ve en la pantalla.
        script = masking_script()
        with_names = script.replace("const NOMBRES_REALES = [];", 'const NOMBRES_REALES = ["Ana María Pérez"];')
        assert with_names != script, "pii-masking.md ya no declara NOMBRES_REALES"
        cls.admin = run_in_chrome(with_names, ADMIN_PAGE)

    def test_every_personal_data_pattern_is_masked(self):
        shown = visible(self.corpus)
        for tipo, text, fragment in PII_POSITIVES:
            with self.subTest(tipo=tipo, text=text):
                self.assertNotIn(fragment, shown)

    def test_ordinary_manual_text_is_left_intact(self):
        shown = visible(self.corpus)
        for text in PII_NEGATIVES:
            with self.subTest(text=text):
                self.assertIn(text, shown)

    def test_reports_what_it_masked_by_type(self):
        counts = self.corpus["result"]["enmascarado"]
        for tipo in {t for t, _, _ in PII_POSITIVES}:
            with self.subTest(tipo=tipo):
                self.assertGreaterEqual(counts.get(tipo, 0), 1, counts)

    def test_admin_screen_shows_no_real_person(self):
        shown = visible(self.admin)
        leaks = ["luis.gomez@cliente.co", "eva@cliente.co", "300 123 4567", "ana.perez@gmail.com",
                 "marta.ruiz@empresa.com", "300 123 4568", "Pedro Díaz Rojas", "jorge@cliente.co", "Ana María Pérez"]
        for leak in leaks:
            with self.subTest(leak=leak):
                self.assertNotIn(leak, shown)
        # Positivo en la misma ejecución: la UI que no es de personas sigue ahí.
        for keep in ["(admin)", "Seleccione...", "Editor", "Administrador", "Escribir al responsable"]:
            with self.subTest(keep=keep):
                self.assertIn(keep, shown)

    def test_value_split_by_a_newline_in_the_html_source_is_masked(self):
        # El navegador pinta el salto como espacio: en la captura el número se ve entero.
        seen = run_in_chrome(masking_script(), "<p>con cédula\n1.023.456.789 registrada</p><pre>llame al 300 123\n4567 hoy</pre><pre>línea 1\nlínea 2</pre>")
        self.assertIn("línea 1\nlínea 2", seen["text"])  # sin datos, el texto queda intacto, saltos incluidos
        shown = seen["text"].replace("\n", " ")
        for fragment in ("1.023.456.789", "300 123 4567"):
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, shown)

    def test_avatar_photos_are_replaced(self):
        self.assertTrue(self.admin["images"], self.admin)
        for src in self.admin["images"]:
            self.assertNotIn("iVBORw0KGgo", src)
        self.assertFalse([b for b in self.admin["backgrounds"] if "iVBORw0KGgo" in b])
        self.assertGreaterEqual(self.admin["result"]["enmascarado"].get("avatar", 0), 2)


AUTH_FLOWS_MD = REPO / "skills" / "app-analyzer" / "references" / "auth-flows.md"
AUTH_MARK = "<!-- auth-secret:script -->"
# Secretos de autenticación que ningún patrón de pii-masking.md detecta (TOTP de 6 dígitos, semilla Base32, códigos de respaldo).
AUTH_PAGE = f"""
<form><input name="otp" autocomplete="one-time-code" value="482913">
  <input class="digit" name="code1" maxlength="1" value="4"><input class="digit" name="code2" maxlength="1" value="8"></form>
<p>Clave para introducir a mano: <code class="totp-secret">JBSWY3DPEHPK3PXP</code></p>
<ul class="recovery-codes"><li>a1b2-c3d4</li><li>e5f6-g7h8</li></ul>
<img class="qr-code" src="{AVATAR_PNG}" width="160" height="160">
<div class="qr"><canvas width="160" height="160"></canvas></div>
<a href="otpauth://totp/Demo:demo@example.com?secret=JBSWY3DPEHPK3PXP">Abrir en la app de autenticación</a>
<p>Introduzca el código de 6 dígitos</p>
"""
# Los mismos secretos sin ninguna marca que un selector reconozca (PoC del revisor): solo los caza la red de respaldo.
AUTH_PAGE_UNMARKED = f"""
<p>Verificación en dos pasos · Paso 2 de 3 · actualizado 2026-10-07 · modo self-host</p>
<input value="KRSXG5CTMVZXI43U">
<p>Clave: JBSW Y3DP EHPK 3PXP</p>
<svg width="240" height="40"><text x="0" y="20">739104</text></svg>
<p>Código enviado: 615 207</p>
<ul><li>k9m2-p4q7</li><li>8812 4409</li></ul>
<div><canvas width="180" height="180"></canvas></div>
<img src="{AVATAR_PNG}" width="200" height="200">
<img src="{AVATAR_PNG}" width="24" height="24" alt="icono">
<span title="Semilla MFZWIZLTOQQGS3TUMVZGI2LP">?</span>
"""


def run_auth(page: str) -> dict:
    snippet = masking_script(AUTH_FLOWS_MD, AUTH_MARK)
    # textContent además de innerText: el texto de un <svg> sale en la captura aunque innerText no lo cuente.
    wrapped = (f"() => ({{ ...({snippet})(), canvas: document.querySelectorAll('canvas').length, "
               "all: (() => { const c = document.body.cloneNode(true); c.querySelectorAll('script').forEach((s) => s.remove()); "
               "return c.textContent; })() })")
    return run_in_chrome(wrapped, page)


@unittest.skipUnless(CHROME, "sin Chrome/Chromium headless")
class TestAuthSecretScript(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seen = run_auth(AUTH_PAGE)
        cls.unmarked = run_auth(AUTH_PAGE_UNMARKED)

    def test_unmarked_secrets_are_caught_by_the_fallback(self):
        shown = visible(self.unmarked) + "\n" + self.unmarked["result"]["all"]
        for leak in ("KRSXG5CTMVZXI43U", "JBSW Y3DP EHPK 3PXP", "739104", "615 207", "k9m2-p4q7", "8812 4409",
                     "MFZWIZLTOQQGS3TUMVZGI2LP"):
            with self.subTest(leak=leak):
                self.assertNotIn(leak, shown)

    def test_unmarked_qr_canvas_and_large_square_image_are_replaced(self):
        self.assertEqual(self.unmarked["result"]["canvas"], 0)
        originals = [s for s in self.unmarked["images"] if "iVBORw0KGgo" in s]
        self.assertEqual(len(originals), 1, self.unmarked["images"])  # solo queda el icono de 24 px

    def test_fallback_leaves_ordinary_ui_text_alone(self):
        shown = visible(self.unmarked)
        for keep in ("Verificación en dos pasos", "Paso 2 de 3", "2026-10-07", "self-host"):
            with self.subTest(keep=keep):
                self.assertIn(keep, shown)

    def test_reports_residue_it_could_not_mask(self):
        # Un secreto partido entre nodos no lo ve el recorrido por nodo de texto, pero sí innerText: el script lo cuenta
        # (sin devolver el texto, que copiaría el secreto al registro de la sesión).
        clean = self.unmarked["result"]["sin_revisar"]
        self.assertEqual(clean["residuo"], 0, clean)
        split = run_auth("<p>Clave: KRSX<b>G5CTMVZXI43U</b>LMNO</p>")["result"]
        self.assertGreaterEqual(split["sin_revisar"]["residuo"], 1, split)
        self.assertNotIn("KRSX", json.dumps(split["sin_revisar"]))

    def test_no_auth_secret_reaches_the_capture(self):
        shown = visible(self.seen)
        for leak in ("482913", "JBSWY3DPEHPK3PXP", "a1b2-c3d4", "e5f6-g7h8", "otpauth:"):
            with self.subTest(leak=leak):
                self.assertNotIn(leak, shown)
        self.assertNotIn("4", self.seen["values"][1:])  # el código partido en una casilla por dígito
        self.assertIn("000000", self.seen["values"])

    def test_qr_is_replaced_not_left_on_screen(self):
        self.assertFalse([s for s in self.seen["images"] if "iVBORw0KGgo" in s], self.seen["images"])
        self.assertEqual(self.seen["result"]["canvas"], 0)

    def test_ui_text_survives(self):
        shown = visible(self.seen)
        for keep in ("Introduzca el código de 6 dígitos", "Abrir en la app de autenticación", "Clave para introducir a mano"):
            with self.subTest(keep=keep):
                self.assertIn(keep, shown)

    def test_guide_does_not_claim_the_token_pattern_covers_2fa(self):
        # El patrón `token` exige prefijos (sk_, ghp_, AKIA, JWT...) o 32+ caracteres: un TOTP de 6 dígitos no lo dispara.
        self.assertNotIn("patrón `token`", AUTH_FLOWS_MD.read_text(encoding="utf-8"))


class TestSingleSource(unittest.TestCase):
    REFS = REPO / "skills" / "screenshot-capturer" / "references"

    def test_both_mcp_guides_link_to_the_single_source_and_carry_no_copy(self):
        for name in ("playwright-mcp.md", "chrome-devtools-mcp.md"):
            text = (self.REFS / name).read_text(encoding="utf-8")
            with self.subTest(guide=name):
                self.assertIn("pii-masking.md", text)
                for copy_marker in ("@[A-Za-z", "[data-user-name]", "img.avatar", "[data-private]", "sanitizado"):
                    self.assertNotIn(copy_marker, text)

    def test_retired_annotation_and_contradiction_are_gone(self):
        for path in [*(REPO / "skills").rglob("*.md"), *(REPO / "commands").glob("*.md"), REPO / "README.md"]:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=str(path.relative_to(REPO))):
                self.assertNotIn("tachado-datos", text)
                self.assertNotIn("nunca decide tachar", text)


if __name__ == "__main__":
    unittest.main()
