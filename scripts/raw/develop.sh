#!/bin/bash
# Develop camera DNGs into finished gallery JPEGs: RawTherapee (AMaZE demosaic, capture sharpening,
# light noise reduction, finish.pp3 look) -> 16-bit TIFF -> finalize.py. Originals are only read.
# Usage: scripts/raw/develop.sh OUTPUT_DIR file1.DNG [file2.DNG ...]
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd); out=$1; shift; mkdir -p "$out/.tif"
for f in "$@"; do
  b=$(basename "$f" .DNG); [ -f "$out/$b.jpg" ] && continue
  rawtherapee-cli -q -o "$out/.tif/$b.tif" -d -p "$here/finish.pp3" -t -b16 -Y -c "$f" >/dev/null
  python3 "$here/finalize.py" "$out/.tif/$b.tif" "$f" "$out/$b.jpg"; rm -f "$out/.tif/$b.tif"; echo "developed $b"
done
