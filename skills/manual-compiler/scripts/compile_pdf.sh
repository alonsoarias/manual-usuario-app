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
Uso: $(basename "$0") --secciones DIR --capturas DIR --plan FILE --brief FILE --output FILE

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
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)/.."
TYPST_TEMPLATE="$PLUGIN_ROOT/assets/manual-template.typ"

# El plugin puede estar instalado en otra ruta cuando se usa como skill;
# permitir override por variable de entorno.
TYPST_TEMPLATE="${MANUAL_USUARIO_APP_TYPST_TEMPLATE:-$TYPST_TEMPLATE}"

if [[ ! -f "$CONCATENATE" ]]; then
    echo "ERROR: no se encontró concatenate.py en $SCRIPT_DIR" >&2
    exit 3
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

mkdir -p "$(dirname "$OUTPUT")"

extract_brief_lang() {
    python3 - "$BRIEF" <<'PYEOF'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
m = re.search(r"^idioma:\s*\"?([a-zA-Z-]+)\"?", text, re.MULTILINE)
print(m.group(1) if m else "es")
PYEOF
}

LANG_BRIEF="$(extract_brief_lang)"

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
    TYP_FINAL="$(mktemp -t manual-final-XXXXXX.typ)"

    pandoc "$CONCAT_TMP" -o "$TYP_TMP" --to=typst

    {
        cat "$TYPST_TEMPLATE"
        echo
        echo "// === inicio del contenido generado ==="
        cat "$TYP_TMP"
    } > "$TYP_FINAL"

    typst compile "$TYP_FINAL" "$OUTPUT"
    return 0
}

compile_with_xelatex() {
    if ! command -v xelatex >/dev/null 2>&1; then
        return 1
    fi
    echo "[2/3] Compilando PDF con XeLaTeX..."

    pandoc "$CONCAT_TMP" \
        -o "$OUTPUT" \
        --pdf-engine=xelatex \
        --toc --toc-depth=3 \
        --number-sections \
        --highlight-style=tango \
        --resource-path="$(dirname "$CAPTURAS"):$CAPTURAS:$SECCIONES" \
        -V mainfont="DejaVu Sans" \
        -V monofont="DejaVu Sans Mono" \
        -V geometry:margin=2.5cm \
        -V lang="$LANG_BRIEF" \
        -V documentclass=report
    return 0
}

compile_with_pdflatex() {
    if ! command -v pdflatex >/dev/null 2>&1; then
        return 1
    fi
    echo "[2/3] Compilando PDF con pdfLaTeX (último recurso)..."

    pandoc "$CONCAT_TMP" \
        -o "$OUTPUT" \
        --pdf-engine=pdflatex \
        --toc --toc-depth=3 \
        --number-sections \
        --highlight-style=tango \
        --resource-path="$(dirname "$CAPTURAS"):$CAPTURAS:$SECCIONES" \
        -V geometry:margin=2.5cm \
        -V lang="$LANG_BRIEF"
    return 0
}

if compile_with_typst; then
    ENGINE="typst"
elif compile_with_xelatex; then
    ENGINE="xelatex"
elif compile_with_pdflatex; then
    ENGINE="pdflatex"
else
    echo "ERROR: no se encontró Typst, XeLaTeX ni pdfLaTeX. Instale alguno para generar PDF." >&2
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
