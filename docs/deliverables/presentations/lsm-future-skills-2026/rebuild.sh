#!/usr/bin/env bash
# Rebuild the LSM Future Skills 2026 proposal flyer.
# Pipeline: Excalidraw source -> SVG -> PDF -> embedded in flyer PDF.
#
# Env quirks hardcoded:
#   - excalidraw-brute-export-cli lives in /tmp/exc-brute (one-off npm install)
#   - rsvg-convert is only in the cogpy conda env (referenced by full path)
#   - quarto's lualatex panics on the conda zlib mismatch from rag env,
#     so LD_LIBRARY_PATH is unset before invoking quarto.
#
# Run from anywhere:
#   bash docs/deliverables/presentations/lsm-future-skills-2026/rebuild.sh
# Or directly:
#   ./rebuild.sh   (from the flyer directory)

set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$DIR/proposal-diagram.excalidraw"
PNG="$DIR/proposal-diagram.png"
QMD="$DIR/proposal-flyer.qmd"

BRUTE_EXPORT="/tmp/exc-brute/node_modules/.bin/excalidraw-brute-export-cli"

# Sanity checks
if [[ ! -x "$BRUTE_EXPORT" ]]; then
  echo "ERROR: tool not found or not executable: $BRUTE_EXPORT" >&2
  exit 1
fi
for src in "$SRC" "$QMD"; do
  if [[ ! -f "$src" ]]; then
    echo "ERROR: source file missing: $src" >&2
    exit 1
  fi
done

echo "==> Exporting Excalidraw to PNG (scale 3 for print clarity)..."
"$BRUTE_EXPORT" -i "$SRC" -o "$PNG" -f png -s 3 -b false 2>&1 | tail -3

echo "==> Rendering flyer PDF (LD_LIBRARY_PATH unset to dodge conda zlib)..."
( unset LD_LIBRARY_PATH; quarto render "$QMD" 2>&1 | tail -3 )

echo "==> Done."
ls -la "$DIR/proposal-flyer.pdf"
