#!/bin/bash
# Develop camera DNGs into finished gallery JPEGs: RawTherapee (AMaZE demosaic, capture sharpening,
# light noise reduction, finish.pp3 look, plus any per-photo profile from adjustments.json) -> 16-bit TIFF
# -> finalize.py (per-photo crop, neutral balance, output size). Frames listed under held_back are skipped.
# Originals are only read. Usage: scripts/raw/develop.sh OUTPUT_DIR file1.DNG [file2.DNG ...]
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd); out=$1; shift; mkdir -p "$out/.tif"
for f in "$@"; do
  b=$(basename "$f" .DNG); [ -f "$out/$b.jpg" ] && continue
  extra=$(python3 -c "import json,sys;a=json.load(open('$here/adjustments.json'));b=sys.argv[1]
print('HOLD' if b in a['held_back'] else next((k for k,v in a['profiles'].items() if b in v),''))" "$b")
  [ "$extra" = HOLD ] && { echo "held back $b"; continue; }
  profiles=(-p "$here/finish.pp3"); [ -n "$extra" ] && profiles+=(-p "$here/$extra.pp3")
  rawtherapee-cli -q -o "$out/.tif/$b.tif" -d "${profiles[@]}" -t -b16 -Y -c "$f" >/dev/null
  python3 "$here/finalize.py" "$out/.tif/$b.tif" "$f" "$out/$b.jpg"; rm -f "$out/.tif/$b.tif"; echo "developed $b"
done
