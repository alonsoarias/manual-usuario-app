#!/usr/bin/env bash
# Compila las secciones del manual en un único archivo DOCX vía Pandoc.
#
# Uso:
#   compile_docx.sh \
#     --secciones {dir} \
#     --capturas {dir} \
#     --plan {ruta} \
#     --brief {ruta} \
#     --output {ruta-docx} \
#     [--reference-doc {ruta-plantilla.docx}]
set -euo pipefail

SECCIONES=""
CAPTURAS=""
PLAN=""
BRIEF=""
OUTPUT=""
REFERENCE_DOC=""

usage() {
    cat <<EOF
Uso: $(basename "$0") --secciones DIR --capturas DIR --plan FILE --brief FILE --output FILE [--reference-doc FILE]

Compila las secciones del manual a DOCX usando Pandoc.

Opciones:
  --secciones DIR        Directorio con secciones .md
  --capturas DIR         Directorio con capturas (PNG)
  --plan FILE            Ruta a 02-plan.md
  --brief FILE           Ruta a 01-brief.md
  --output FILE          Archivo DOCX de salida
  --reference-doc FILE   (Opcional) Plantilla DOCX del cliente con membrete
  -h, --help             Muestra esta ayuda
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --secciones)      SECCIONES="$2"; shift 2 ;;
        --capturas)       CAPTURAS="$2";  shift 2 ;;
        --plan)           PLAN="$2";      shift 2 ;;
        --brief)          BRIEF="$2";     shift 2 ;;
        --output)         OUTPUT="$2";    shift 2 ;;
        --reference-doc)  REFERENCE_DOC="$2"; shift 2 ;;
        -h|--help)        usage; exit 0 ;;
        *)                echo "Opción desconocida: $1" >&2; usage; exit 2 ;;
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
    echo "ERROR: pandoc no está instalado o no está en PATH" >&2
    exit 3
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 no está instalado o no está en PATH" >&2
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

if [[ ! -f "$CONCATENATE" ]]; then
    echo "ERROR: no se encontró concatenate.py en $SCRIPT_DIR" >&2
    exit 3
fi

CONCAT_TMP="$(mktemp -t manual-concat-XXXXXX.md)"
trap 'rm -f "$CONCAT_TMP"' EXIT

echo "[1/3] Concatenando secciones..."
python3 "$CONCATENATE" \
    --secciones "$SECCIONES" \
    --capturas "$CAPTURAS" \
    --plan "$PLAN" \
    --brief "$BRIEF" \
    --output "$CONCAT_TMP"

mkdir -p "$(dirname "$OUTPUT")"

echo "[2/3] Compilando DOCX con Pandoc..."
# Markdown no confiable (lo redactan agentes): sin {=openxml} crudo ni matemáticas; mismo --from que la validación.
PANDOC_ARGS=(
    --from="$PANDOC_FROM"
    "$CONCAT_TMP"
    -o "$OUTPUT"
    --toc
    --toc-depth=3
    --number-sections
    --highlight-style=tango
    --resource-path="$(dirname "$CAPTURAS"):$CAPTURAS:$SECCIONES"
)

TRUSTED_REFERENCE=""
if [[ -n "$REFERENCE_DOC" ]]; then
    if [[ -f "$REFERENCE_DOC" ]]; then
        TRUSTED_REFERENCE="$REFERENCE_DOC"
        PANDOC_ARGS+=(--reference-doc="$REFERENCE_DOC")
        echo "    Usando plantilla de referencia: $REFERENCE_DOC"
    else
        echo "    AVISO: --reference-doc apuntaba a $REFERENCE_DOC, no existe; compilando sin plantilla" >&2
    fi
fi

pandoc "${PANDOC_ARGS[@]}"

echo "[3/3] Verificando salida..."
if [[ ! -f "$OUTPUT" ]]; then
    echo "ERROR: no se generó el DOCX en $OUTPUT" >&2
    exit 4
fi

# Defensa en profundidad: los medios que añade el CONTENIDO a word/media sólo pueden ser imágenes (un archivo
# ajeno embebido = fuga). Los que ya trae la plantilla del cliente (--reference-doc, archivo de confianza)
# se ignoran: pandoc los copia tal cual (logo.emf, etc.).
BAD_MEDIA="$(python3 - "$OUTPUT" "$TRUSTED_REFERENCE" <<'PYEOF'
import sys
import zipfile

IMAGE_EXTENSIONS = {
    "png", "jpg", "jpeg", "gif", "svg", "webp",  # web y capturas
    "bmp", "tif", "tiff", "ico",  # ráster
    "emf", "wmf", "eps", "pdf",  # vectoriales y de documento
}
MEDIA = "word/media/"


def media(path):
    with zipfile.ZipFile(path) as z:
        return [n for n in z.namelist() if n.startswith(MEDIA)]


trusted = set(media(sys.argv[2])) if sys.argv[2] else set()
print(" ".join(n for n in media(sys.argv[1])
               if n not in trusted and n.rsplit(".", 1)[-1].lower() not in IMAGE_EXTENSIONS))
PYEOF
)" || BAD_MEDIA="(DOCX ilegible)"
if [[ -n "$BAD_MEDIA" ]]; then
    rm -f "$OUTPUT"
    echo "ERROR: word/media contiene archivos que no son imágenes: $BAD_MEDIA" >&2
    exit 7
fi

SIZE_BYTES=$(wc -c < "$OUTPUT")
SIZE_MB=$(awk -v b="$SIZE_BYTES" 'BEGIN { printf "%.2f", b/1024/1024 }')
echo "OK — DOCX generado: $OUTPUT (${SIZE_MB} MB)"

if [[ "$SIZE_BYTES" -lt 102400 ]]; then
    echo "AVISO: tamaño del DOCX por debajo de 100 KB, revisar contenido" >&2
fi
if [[ "$SIZE_BYTES" -gt 31457280 ]]; then
    echo "AVISO: tamaño del DOCX por encima de 30 MB, revisar capturas embebidas" >&2
fi

exit 0
