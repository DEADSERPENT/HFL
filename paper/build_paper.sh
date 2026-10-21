#!/usr/bin/env bash
#==============================================================================
# build_paper.sh — compile the PP-HFM manuscript and report what went wrong.
#
# Lives OUTSIDE paper/ so build products never land in the source tree and the
# paper folder stays exactly what you upload to Overleaf.
#
# Usage:
#   ./build_paper.sh              build paper/main.tex
#   ./build_paper.sh --clean      remove build products first
#   ./build_paper.sh --quiet      only print the diagnosis, not the TeX chatter
#   ./build_paper.sh <dir>        build a different project directory
#
# Why the four passes: pdflatex resolves references from the .aux written by
# the PREVIOUS pass, so one run leaves every \ref as "??". bibtex then needs an
# .aux containing the \citation entries, and two further passes are needed for
# the bibliography to appear and for the reference numbers to settle.
#==============================================================================
set -uo pipefail

PROJ="paper"
CLEAN=0
QUIET=0
for a in "$@"; do
  case "$a" in
    --clean) CLEAN=1 ;;
    --quiet) QUIET=1 ;;
    -*)      echo "unknown flag: $a"; exit 2 ;;
    *)       PROJ="$a" ;;
  esac
done

MAIN="main"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# The header says this script lives beside the project, but it is currently
# INSIDE it. Resolve both layouts instead of assuming one: if main.tex sits
# next to the script and no project was named on the command line, the script
# is inside the project and the build root is its parent.
if [ -f "$HERE/$MAIN.tex" ] && [ "$PROJ" = "paper" ]; then
  SRC="$HERE"
  ROOT="$(dirname "$HERE")"
else
  SRC="$HERE/$PROJ"
  ROOT="$HERE"
fi
OUT="$ROOT/build/$(basename "$SRC")"

[ -f "$SRC/$MAIN.tex" ] || { echo "[FATAL] no $SRC/$MAIN.tex"; exit 1; }

# ── toolchain ────────────────────────────────────────────────────────────────
ENGINE=""
command -v latexmk  >/dev/null && ENGINE="latexmk"
[ -z "$ENGINE" ] && command -v pdflatex >/dev/null && ENGINE="pdflatex"
[ -z "$ENGINE" ] && command -v tectonic >/dev/null && ENGINE="tectonic"

if [ -z "$ENGINE" ]; then
  cat <<'EOS'
[FATAL] No LaTeX toolchain found (looked for latexmk, pdflatex, tectonic).

Install one, then re-run this script. The smallest install that compiles an
IEEEtran paper with algorithms and BibTeX:

    sudo apt-get install --no-install-recommends \
        texlive-latex-recommended texlive-latex-extra texlive-science \
        texlive-fonts-recommended texlive-publishers latexmk

texlive-publishers is NOT optional: it carries IEEEtran.cls, and without it
the very first line of main.tex fails. biber is NOT needed -- main.tex uses
\bibliographystyle + \bibliography, which is BibTeX, not biblatex.

(That needs your password, so run it yourself — in this session prefix it with
an exclamation mark: !sudo apt-get install ...)

Until then, Overleaf remains the build. This script only automates a local one.
EOS
  exit 3
fi

mkdir -p "$OUT"
if [ "$CLEAN" = 1 ]; then rm -rf "${OUT:?}"/*; echo "[clean] $OUT emptied"; fi

echo "[build] engine=$ENGINE  src=$SRC  out=$OUT"
cd "$SRC" || exit 1

run() {  # run <label> <command...>
  if [ "$QUIET" = 1 ]; then "${@:2}" >/dev/null 2>&1
  else "${@:2}" 2>&1 | sed "s/^/    [$1] /" | tail -5
  fi
  return "${PIPESTATUS[0]}"
}

if [ "$ENGINE" = "latexmk" ]; then
  run latexmk latexmk -pdf -interaction=nonstopmode -file-line-error \
      -outdir="$OUT" "$MAIN.tex"
elif [ "$ENGINE" = "tectonic" ]; then
  # --keep-logs is REQUIRED, not optional: tectonic discards intermediates by
  # default, so without it there is no main.log, every grep below finds
  # nothing, and the script reports a clean build no matter what happened.
  run tectonic tectonic -o "$OUT" --keep-logs "$MAIN.tex"
else
  # Explicit four-pass sequence. Not halt-on-error: a missing reference should
  # not abort a build whose whole purpose is to report missing references.
  run "pass 1" pdflatex -interaction=nonstopmode -file-line-error \
      -output-directory="$OUT" "$MAIN.tex"
  if grep -q '\\citation' "$OUT/$MAIN.aux" 2>/dev/null; then
    ( cd "$OUT" && run bibtex bibtex "$MAIN" )
  fi
  run "pass 2" pdflatex -interaction=nonstopmode -file-line-error \
      -output-directory="$OUT" "$MAIN.tex"
  run "pass 3" pdflatex -interaction=nonstopmode -file-line-error \
      -output-directory="$OUT" "$MAIN.tex"
fi

LOG="$OUT/$MAIN.log"
PDF="$OUT/$MAIN.pdf"

echo
echo "=============================================================="
echo "  DIAGNOSIS"
echo "=============================================================="

if [ ! -f "$PDF" ]; then
  echo "  NO PDF PRODUCED."
  [ -f "$LOG" ] && { echo "  first errors:"; grep -E "^![[:space:]]|^.*:[0-9]+:" "$LOG" | head -12 | sed 's/^/    /'; }
  exit 4
fi

pages=$(grep -oE "Output written .*\(([0-9]+) page" "$LOG" 2>/dev/null | grep -oE "[0-9]+ page" | grep -oE "[0-9]+")
size=$(du -h "$PDF" | cut -f1)
echo "  PDF: $PDF  (${pages:-?} pages, $size)"

# Things that silently degrade a submission and that a structural check
# cannot see. Each is counted, and listed only if present.
report() {  # report <label> <grep-pattern> [max-lines]
  local n
  n=$(grep -cE "$2" "$LOG" 2>/dev/null || true)
  if [ "${n:-0}" -gt 0 ]; then
    echo "  $1: $n"
    grep -E "$2" "$LOG" | head -"${3:-4}" | sed 's/^/      /'
  else
    echo "  $1: none"
  fi
}

report "errors"              "^!|^.*:[0-9]+: " 8
report "undefined refs"      "Reference .* undefined" 6
report "undefined citations" "Citation .* undefined" 6
report "multiply-defined"    "multiply defined" 4
report "overfull boxes"      "Overfull \\\\hbox" 4
report "underfull boxes"     "Underfull \\\\hbox" 3
report "float warnings"      "float specifier|too many unprocessed floats|Float too large" 4
report "missing figures"     "File .* not found|Unable to load picture" 4

echo
echo "  NOTE ON FLOATS: 'too many unprocessed floats' or figures drifting far"
echo "  from their reference usually means a figure* could not be placed. The"
echo "  fixes, in order: keep stfloats loaded; declare the float earlier in the"
echo "  source; or make it single-column if the content allows."
echo "=============================================================="
cp -f "$PDF" "$SRC/$(basename "$SRC")_build.pdf" 2>/dev/null && \
  echo "  copy: $SRC/$(basename "$SRC")_build.pdf"

# Only ever write to <project>_build.pdf. Other PDFs beside the sources are NOT
# build outputs -- paper/IEEE_RESEARCH_HFL.pdf is downloaded from Overleaf --
# and overwriting them would destroy a separately maintained artefact.
