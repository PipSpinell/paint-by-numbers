#!/usr/bin/env bash
# Usage: ./make_sheet.sh path/to/image.png [output_dir]
# Builds the full kit for one image: 2-page A4 sheet (PNG + vector PDF), marker demo and step-by-step HTML guide.
set -euo pipefail
T="$(cd "$(dirname "$0")/pbn" && pwd)"
SRC="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
base="$(basename "${SRC%.*}")"
OUT="${2:-out}/$base"
mkdir -p "$OUT"; cd "$OUT"
export PBN_NOME="${PBN_NOME:-$(python3 "$T/nome.py" "$base")}"
export PBN_SLUG="${PBN_SLUG:-$(echo "$base" | sed -E 's/^[0-9]+_//; s/_+/_/g' | tr 'A-Z' 'a-z')}"
python3 "$T/0_consiglia_colori.py" "$SRC" 6 16 > colours.txt          # picks the number of colours
K=$(grep -o 'CONSIGLIATI: [0-9]*' colours.txt | awk '{print $2}')
python3 "$T/1_quantizza.py" "$SRC" . 1100 "$K" > quantize.log       # palette, zones, printed name/signature
python3 "$T/2_tavola_png_pdf.py" . > sheet.log                       # PNG pages at 300 dpi
python3 "$T/3_vettoriali.py" > vector.log                            # 2-page vector PDF + SVG
python3 "$T/6_demo_pennarello.py" > /dev/null                        # marker demo
python3 "$T/7_guida_passo_passo.py" > guide.log                      # step-by-step HTML guide
rm -f state.pkl printed.png
echo "$PBN_NOME: $(grep -o 'colori [0-9]*' sheet.log | awk '{print $2}') colours -> $OUT"
