#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p .build
if [[ "${1:-}" == "--figures" ]]; then
  export MPLCONFIGDIR="${TMPDIR:-/tmp}/intellisys-paper-matplotlib"
  "${PYTHON:-python3}" scripts/make_figures.py
fi
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=.build manuscript.tex > .build/build-pass1.txt
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=.build manuscript.tex > .build/build-pass2.txt
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=.build manuscript.tex > .build/build-pass3.txt
cp .build/manuscript.pdf manuscript.pdf
printf 'Built manuscript.pdf\n'
