#!/usr/bin/env bash
set -euo pipefail
paper_directory="$(cd "$(dirname "$0")" && pwd)"
cd "$paper_directory"
export TEXINPUTS="$paper_directory/template:${TEXINPUTS:-}:"
export BSTINPUTS="$paper_directory/template:${BSTINPUTS:-}:"
latexmk -pdf -interaction=nonstopmode -halt-on-error manuscript.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error author_review.tex
