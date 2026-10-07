#!/usr/bin/env bash
# Compila las secciones del manual en un único archivo PDF.
# Estrategia: Typst (preferido) -> XeLaTeX (fallback) -> pdfLaTeX (último recurso).
#
# Uso:
#   compile_pdf.sh \
#     --secciones {dir} \
#     --capturas {dir} \
#     --plan {ruta} \
#     --brief {ruta} \
#     --output {ruta-pdf}
set -euo pipefail

SECCIONES=""
CAPTURAS=""
PLAN=""
BRIEF=""
OUTPUT=""

usage() {
    cat <<EOF
Uso: ${0##*/} --secciones DIR --capturas DIR --plan FILE --brief FILE --output FILE

Compila las secciones del manual a PDF.

Estrategia:
  1. Typst (si typst está disponible y existe la plantilla del plugin)
  2. XeLaTeX (si xelatex está disponible)
  3. pdfLaTeX (último recurso, sólo para contenido ASCII)

Opciones:
  --secciones DIR    Directorio con secciones .md
  --capturas DIR     Directorio con capturas
  --plan FILE        Ruta a 02-plan.md
  --brief FILE       Ruta a 01-brief.md
  --output FILE      Archivo PDF de salida
  -h, --help         Muestra esta ayuda
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --secciones) SECCIONES="$2"; shift 2 ;;
        --capturas)  CAPTURAS="$2";  shift 2 ;;
        --plan)      PLAN="$2";      shift 2 ;;
        --brief)     BRIEF="$2";     shift 2 ;;
        --output)    OUTPUT="$2";    shift 2 ;;
        -h|--help)   usage; exit 0 ;;
        *)           echo "Opción desconocida: $1" >&2; usage; exit 2 ;;
    esac
done

for var in SECCIONES CAPTURAS PLAN BRIEF OUTPUT; do
    if [[ -z "${!var}" ]]; then
        echo "ERROR: falta --${var,,}" >&2
        usage
        exit 2
    fi
done

if ! command -v pandoc >/dev/null 2>&1; then
    echo "ERROR: pandoc no está instalado" >&2
    exit 3
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 no está instalado" >&2
    exit 3
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONCATENATE="$SCRIPT_DIR/concatenate.py"

# Única fuente del --from de pandoc (la comparte concatenate.py): el parse debe ser idéntico en validación y motor.
if [[ ! -f "$SCRIPT_DIR/pandoc-from.txt" ]]; then
    echo "ERROR: no se encontró pandoc-from.txt en $SCRIPT_DIR" >&2
    exit 3
fi
PANDOC_FROM="$(<"$SCRIPT_DIR/pandoc-from.txt")"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)/.."
TYPST_TEMPLATE="$PLUGIN_ROOT/assets/manual-template.typ"

# El plugin puede estar instalado en otra ruta cuando se usa como skill;
# permitir override por variable de entorno.
TYPST_TEMPLATE="${MANUAL_USUARIO_APP_TYPST_TEMPLATE:-$TYPST_TEMPLATE}"

if [[ ! -f "$CONCATENATE" ]]; then
    echo "ERROR: no se encontró concatenate.py en $SCRIPT_DIR" >&2
    exit 3
fi

OUT_DIR="$(dirname "$OUTPUT")"
mkdir -p "$OUT_DIR"
# Sin esto, un PDF de una corrida anterior hace pasar por buena una compilación que falló.
rm -f "$OUTPUT"

# salida/compilacion.log: lo mismo que se ve en consola (stdout y stderr), en modo append. Las dos tee corren
# fuera del script: no cambian su código de salida.
LOG="$OUT_DIR/compilacion.log"
echo "=== ${0##*/} $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" >> "$LOG"
exec > >(tee -a "$LOG") 2> >(tee -a "$LOG" >&2)

# El contenido lo redactan agentes: un enlace simbólico en secciones/ o capturas/ puede apuntar fuera
# del manual (Typst los sigue aunque estén fuera de --root). `find` también detecta que el propio
# directorio sea un enlace.
if [[ -n "$(find "$SECCIONES" "$CAPTURAS" -type l -print -quit)" ]]; then
    echo "ERROR: secciones/ o capturas/ contienen enlaces simbólicos; se rechazan por seguridad." >&2
    exit 6
fi

CONCAT_TMP="$(mktemp -t manual-concat-XXXXXX.md)"
trap 'rm -f "$CONCAT_TMP" "${TYP_TMP:-}" "${TYP_FINAL:-}"' EXIT

echo "[1/3] Concatenando secciones..."
python3 "$CONCATENATE" \
    --secciones "$SECCIONES" \
    --capturas "$CAPTURAS" \
    --plan "$PLAN" \
    --brief "$BRIEF" \
    --output "$CONCAT_TMP"

# El Markdown lo redactan agentes a partir de la app analizada: no es de confianza.
# Typst sólo puede leer dentro del ancestro común de secciones/ y capturas/, y pandoc no
# convierte bloques ```{=typst} del Markdown en código Typst (raw_attribute apagada).
SANDBOX_ROOT="$(python3 -c 'import os, sys; print(os.path.commonpath([os.path.realpath(p) for p in sys.argv[1:]]))' "$SECCIONES" "$CAPTURAS")"

extract_brief_lang() {
    python3 - "$BRIEF" <<'PYEOF'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
m = re.search(r"^idioma:\s*\"?([a-zA-Z-]+)\"?", text, re.MULTILINE)
print(m.group(1) if m else "es")
PYEOF
}

LANG_BRIEF="$(extract_brief_lang)"

# Devuelve 0 si compiló, 1 si Typst no está disponible (se prueba LaTeX) y 2 si Typst está y FALLÓ:
# un fallo provocable desde el contenido no puede degradar a LaTeX (fail-closed).
compile_with_typst() {
    if ! command -v typst >/dev/null 2>&1; then
        return 1
    fi
    if [[ ! -f "$TYPST_TEMPLATE" ]]; then
        echo "    Plantilla Typst no encontrada en $TYPST_TEMPLATE; usando estrategia 2." >&2
        return 1
    fi
    echo "[2/3] Compilando PDF con Typst..."

    TYP_TMP="$(mktemp -t manual-body-XXXXXX.typ)"
    # El .typ final vive dentro de la raíz: Typst resuelve las rutas absolutas contra --root.
    TYP_FINAL="$(mktemp -p "$SANDBOX_ROOT" .manual-final-XXXXXX.typ)" || return 2

    pandoc --from="$PANDOC_FROM" "$CONCAT_TMP" -o "$TYP_TMP" --to=typst || return 2

    # En Typst `/ruta` es relativa a --root: las imágenes (absolutas para pandoc) pasan a ser relativas a la raíz.
    # Las que apuntan fuera de la raíz quedan como `/ruta/ajena`, que Typst no encuentra: falla en vez de leerlas.
    python3 - "$TYP_TMP" "$SANDBOX_ROOT" <<'PYEOF'
import sys
path, root = sys.argv[1], sys.argv[2].rstrip("/")
text = open(path, encoding="utf-8").read()
open(path, "w", encoding="utf-8").write(text.replace(f'image("{root}/', 'image("/'))
PYEOF

    {
        cat "$TYPST_TEMPLATE"
        echo
        echo "// === inicio del contenido generado ==="
        cat "$TYP_TMP"
    } > "$TYP_FINAL"

    # Dentro de `if`/`||` errexit no aplica: el fallo se devuelve explícitamente.
    if ! typst compile --root "$SANDBOX_ROOT" --input "lang=$LANG_BRIEF" "$TYP_FINAL" "$OUTPUT"; then
        return 2
    fi
    return 0
}

compile_with_xelatex() {
    if ! command -v xelatex >/dev/null 2>&1; then
        return 1
    fi
    echo "[2/3] Compilando PDF con XeLaTeX..."

    # fontspec aborta si la fuente no existe: sólo se fuerzan las que fc-list lista (familia exacta).
    local fonts font_args=()
    fonts="$(fc-list : family 2>/dev/null | tr ',' '\n' || true)"
    grep -qixF "DejaVu Sans" <<<"$fonts" && font_args+=(-V mainfont="DejaVu Sans")
    grep -qixF "DejaVu Sans Mono" <<<"$fonts" && font_args+=(-V monofont="DejaVu Sans Mono")

    if ! pandoc --from="$PANDOC_FROM" "$CONCAT_TMP" \
        -o "$OUTPUT" \
        --pdf-engine=xelatex \
        --toc --toc-depth=3 \
        --number-sections \
        --highlight-style=tango \
        --resource-path="$(dirname "$CAPTURAS"):$CAPTURAS:$SECCIONES" \
        "${font_args[@]}" \
        -V geometry:margin=2.5cm \
        -V lang="$LANG_BRIEF" \
        -V documentclass=report; then
        echo "    AVISO: XeLaTeX falló: ¿fuente DejaVu Sans o babel-$LANG_BRIEF sin instalar? Ver fc-list y tlmgr; probando pdfLaTeX." >&2
        return 1
    fi
    return 0
}

compile_with_pdflatex() {
    if ! command -v pdflatex >/dev/null 2>&1; then
        return 1
    fi
    echo "[2/3] Compilando PDF con pdfLaTeX (último recurso)..."

    if ! pandoc --from="$PANDOC_FROM" "$CONCAT_TMP" \
        -o "$OUTPUT" \
        --pdf-engine=pdflatex \
        --toc --toc-depth=3 \
        --number-sections \
        --highlight-style=tango \
        --resource-path="$(dirname "$CAPTURAS"):$CAPTURAS:$SECCIONES" \
        -V geometry:margin=2.5cm \
        -V lang="$LANG_BRIEF"; then
        echo "    AVISO: pdfLaTeX falló (¿babel-$LANG_BRIEF sin instalar?)." >&2
        return 1
    fi
    return 0
}

TYPST_RC=0
compile_with_typst || TYPST_RC=$?
if [[ "$TYPST_RC" -eq 2 ]]; then
    echo "ERROR: Typst falló y no se usa LaTeX como alternativa (el contenido no es de confianza). Corrija el error de Typst de arriba." >&2
    exit 5
fi

if [[ "$TYPST_RC" -eq 0 ]]; then
    ENGINE="typst"
elif compile_with_xelatex; then
    ENGINE="xelatex"
elif compile_with_pdflatex; then
    ENGINE="pdflatex"
else
    echo "ERROR: no se pudo generar el PDF: Typst, XeLaTeX y pdfLaTeX no están instalados o fallaron (ver avisos)." >&2
    exit 4
fi

echo "[3/3] Verificando salida..."
if [[ ! -f "$OUTPUT" ]]; then
    echo "ERROR: no se generó el PDF en $OUTPUT (motor: $ENGINE)" >&2
    exit 5
fi

SIZE_BYTES=$(wc -c < "$OUTPUT")
SIZE_MB=$(awk -v b="$SIZE_BYTES" 'BEGIN { printf "%.2f", b/1024/1024 }')
echo "OK — PDF generado con $ENGINE: $OUTPUT (${SIZE_MB} MB)"

if [[ "$SIZE_BYTES" -lt 524288 ]]; then
    echo "AVISO: tamaño del PDF por debajo de 0.5 MB, revisar contenido" >&2
fi
if [[ "$SIZE_BYTES" -gt 52428800 ]]; then
    echo "AVISO: tamaño del PDF por encima de 50 MB, revisar capturas embebidas" >&2
fi

exit 0
