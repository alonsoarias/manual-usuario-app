#!/usr/bin/env bash
# Compila las secciones del manual con Pandoc a DOCX, HTML autocontenido o Markdown (GFM).
#
# Uso:
#   compile_pandoc.sh \
#     --to docx|html|gfm \
#     --secciones {dir} \
#     --capturas {dir} \
#     --plan {ruta} \
#     --brief {ruta} \
#     --output {ruta-salida} \
#     [--reference-doc {ruta-plantilla.docx}]   (sólo docx)
set -euo pipefail

TO=""
SECCIONES=""
CAPTURAS=""
PLAN=""
BRIEF=""
OUTPUT=""
REFERENCE_DOC=""

usage() {
    cat <<EOF
Uso: ${0##*/} --to docx|html|gfm --secciones DIR --capturas DIR --plan FILE --brief FILE --output FILE [--reference-doc FILE]

Compila las secciones del manual con Pandoc.

Formatos (--to):
  docx   DOCX (--output: archivo .docx)
  html   HTML autocontenido, imágenes embebidas (--output: archivo .html)
  gfm    Markdown GFM (--output: archivo .md); las imágenes se copian a web/ junto a él

Opciones:
  --to FORMATO           docx, html o gfm
  --secciones DIR        Directorio con secciones .md
  --capturas DIR         Directorio con capturas (PNG)
  --plan FILE            Ruta a 02-plan.md
  --brief FILE           Ruta a 01-brief.md
  --output FILE          Archivo de salida
  --reference-doc FILE   (Opcional, sólo docx) Plantilla DOCX del cliente con membrete
  -h, --help             Muestra esta ayuda
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --to)             TO="$2";        shift 2 ;;
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

for var in TO SECCIONES CAPTURAS PLAN BRIEF OUTPUT; do
    if [[ -z "${!var}" ]]; then
        echo "ERROR: falta --${var,,}" >&2
        usage
        exit 2
    fi
done

case "$TO" in
    docx|html|gfm) ;;
    *) echo "ERROR: --to debe ser docx, html o gfm (recibido: $TO)" >&2; usage; exit 2 ;;
esac

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

OUT_DIR="$(dirname "$OUTPUT")"
mkdir -p "$OUT_DIR"
# Sin esto, una salida de una corrida anterior hace pasar por buena una compilación que falló.
rm -f "$OUTPUT"

# salida/compilacion.log: lo mismo que se ve en consola (stdout y stderr), en modo append. Las dos tee corren
# fuera del script: no cambian su código de salida.
LOG="$OUT_DIR/compilacion.log"
echo "=== ${0##*/} --to $TO $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" >> "$LOG"
exec > >(tee -a "$LOG") 2> >(tee -a "$LOG" >&2)

CONCAT_TMP="$(mktemp -t manual-concat-XXXXXX.md)"
trap 'rm -f "$CONCAT_TMP"' EXIT

echo "[1/3] Concatenando secciones..."
python3 "$CONCATENATE" \
    --secciones "$SECCIONES" \
    --capturas "$CAPTURAS" \
    --plan "$PLAN" \
    --brief "$BRIEF" \
    --output "$CONCAT_TMP"

# Rutas absolutas: gfm ejecuta pandoc desde el directorio de salida (las imágenes salen con ruta relativa a él).
SECCIONES="$(cd "$SECCIONES" && pwd)"
CAPTURAS="$(cd "$CAPTURAS" && pwd)"
OUT_DIR="$(cd "$OUT_DIR" && pwd)"
OUT_FILE="$OUT_DIR/${OUTPUT##*/}"

echo "[2/3] Compilando ${TO^^} con Pandoc..."
# Markdown no confiable (lo redactan agentes): sin HTML/{=openxml}/TeX crudo ni matemáticas; mismo --from que la validación.
PANDOC_ARGS=(
    --from="$PANDOC_FROM"
    "$CONCAT_TMP"
    -o "$OUT_FILE"
    --resource-path="$(dirname "$CAPTURAS"):$CAPTURAS:$SECCIONES"
)

case "$TO" in
    docx)
        PANDOC_ARGS+=(--to=docx --toc --toc-depth=3 --number-sections --highlight-style=tango)
        ;;
    html)
        PANDOC_ARGS+=(--to=html5 -s --embed-resources --toc --toc-depth=3 --number-sections --highlight-style=tango)
        ;;
    gfm)
        # Markdown sin HTML en la salida; imágenes copiadas a web/ con ruta relativa al .md.
        PANDOC_ARGS+=(--to=gfm-raw_html --wrap=none --extract-media=web)
        ;;
esac

TRUSTED_REFERENCE=""
if [[ -n "$REFERENCE_DOC" && "$TO" != docx ]]; then
    echo "    AVISO: --reference-doc sólo aplica a --to docx; se ignora" >&2
elif [[ -n "$REFERENCE_DOC" ]]; then
    if [[ -f "$REFERENCE_DOC" ]]; then
        TRUSTED_REFERENCE="$REFERENCE_DOC"
        PANDOC_ARGS+=(--reference-doc="$REFERENCE_DOC")
        echo "    Usando plantilla de referencia: $REFERENCE_DOC"
    else
        echo "    AVISO: --reference-doc apuntaba a $REFERENCE_DOC, no existe; compilando sin plantilla" >&2
    fi
fi

(cd "$OUT_DIR" && pandoc "${PANDOC_ARGS[@]}")

echo "[3/3] Verificando salida..."
if [[ ! -f "$OUT_FILE" ]]; then
    echo "ERROR: no se generó la salida en $OUTPUT" >&2
    exit 4
fi

# Defensa en profundidad (sólo docx): los medios que añade el CONTENIDO a word/media sólo pueden ser imágenes (un
# archivo ajeno embebido = fuga). Los que ya trae la plantilla del cliente (--reference-doc, archivo de confianza)
# se ignoran: pandoc los copia tal cual (logo.emf, etc.).
docx_foreign_media() {
    python3 - "$OUT_FILE" "$TRUSTED_REFERENCE" <<'PYEOF'
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
}

if [[ "$TO" == docx ]]; then
    BAD_MEDIA="$(docx_foreign_media)" || BAD_MEDIA="(DOCX ilegible)"
    if [[ -n "$BAD_MEDIA" ]]; then
        rm -f "$OUT_FILE"
        echo "ERROR: word/media contiene archivos que no son imágenes: $BAD_MEDIA" >&2
        exit 7
    fi
fi

SIZE_BYTES=$(wc -c < "$OUT_FILE")
SIZE_MB=$(awk -v b="$SIZE_BYTES" 'BEGIN { printf "%.2f", b/1024/1024 }')
case "$TO" in
    docx) LABEL="DOCX" ;;
    html) LABEL="HTML" ;;
    gfm)  LABEL="Markdown" ;;
esac
echo "OK — $LABEL generado: $OUTPUT (${SIZE_MB} MB)"

if [[ "$TO" == docx ]]; then
    if [[ "$SIZE_BYTES" -lt 102400 ]]; then
        echo "AVISO: tamaño del DOCX por debajo de 100 KB, revisar contenido" >&2
    fi
    if [[ "$SIZE_BYTES" -gt 31457280 ]]; then
        echo "AVISO: tamaño del DOCX por encima de 30 MB, revisar capturas embebidas" >&2
    fi
fi

exit 0
