#!/usr/bin/env bash
#==============================================================================
# make_overleaf.sh — package this manuscript (PLDP) for Overleaf, test-compile
# the package from a clean copy, and zip it.
#
#   bash PLDP/make_overleaf.sh
#
# Output: <repo>/PLDP_overleaf.zip (files at the zip root, so Overleaf's
# "Upload Project" opens main.tex directly) and <repo>/PLDP.pdf. Only the
# figures that main.tex and sections/ include are packaged; build scripts are
# left out. Re-run after any edit.
#==============================================================================
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SRC")"
ZIP="$ROOT/PLDP_overleaf.zip"
PKG="$(mktemp -d)"; TMP="$(mktemp -d)"
trap 'rm -rf "$PKG" "$TMP"' EXIT

mkdir -p "$PKG/sections" "$PKG/figures"
cp "$SRC/main.tex" "$SRC/references.bib" "$PKG/"
cp "$SRC"/sections/*.tex "$PKG/sections/"
grep -oh '\\includegraphics\(\[[^]]*\]\)\?{[^}]*}' "$SRC/main.tex" "$SRC"/sections/*.tex \
  | sed 's/.*{\(.*\)}/\1/' | sort -u | while read -r f; do
    [[ -f "$SRC/figures/$f" ]] || { echo "[FAIL] missing figure $f"; exit 1; }
    cp "$SRC/figures/$f" "$PKG/figures/"
  done
cat > "$PKG/README.txt" <<'EOF'
PLDP: Patient-Level Differential Privacy in Hierarchical Federated Learning
for Multimodal Medical IoT

Overleaf: New Project > Upload Project > select PLDP_overleaf.zip.
Compiler: pdfLaTeX (Menu > Settings). Main document: main.tex.
Class IEEEtran and style IEEEtran.bst are provided by Overleaf's TeX Live.

main.tex          preamble, title, authors, section order
sections/*.tex    abstract ... conclusion, data availability, acknowledgment
references.bib    bibliography (IEEEtran style)
figures/          vector PDF figures, all referenced from sections/
EOF

# test compile from a clean copy, so nothing outside the package is relied on
cp -r "$PKG"/. "$TMP/"
( cd "$TMP" && tectonic -X compile --keep-logs main.tex >/dev/null 2>&1 ) \
  || { echo "[FAIL] clean compile failed"; tail -20 "$TMP/main.log"; exit 1; }
# only real reference/citation problems (tectonic's XeTeX also logs font-shape
# substitutions as "undefined"; pdfLaTeX on Overleaf does not)
if grep -E "(Reference|Citation).*undefined|There were undefined" "$TMP/main.log" >/dev/null; then
  echo "[FAIL] undefined references or citations:"
  grep -E "(Reference|Citation).*undefined" "$TMP/main.log" | head; exit 1
fi
pages=$(pdfinfo "$TMP/main.pdf" 2>/dev/null | awk '/^Pages/{print $2}')
cp "$TMP/main.pdf" "$ROOT/PLDP.pdf"

rm -f "$ZIP"
( cd "$PKG" && zip -qr "$ZIP" . )
echo "package: $(find "$PKG" -type f | wc -l) files, clean compile ${pages} pages"
echo "zip: $ZIP ($(du -h "$ZIP" | cut -f1))"
echo "pdf: $ROOT/PLDP.pdf"
