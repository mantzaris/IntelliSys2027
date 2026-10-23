#!/usr/bin/env bash
set -euo pipefail
PCC_PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PCC_PROJECT_ROOT/paper"
export TEXINPUTS="$PCC_PROJECT_ROOT/artifacts/public_assets:${TEXINPUTS:-}:"
export BSTINPUTS="$PCC_PROJECT_ROOT/artifacts/public_assets:${BSTINPUTS:-}:"
latexmk -pdf -interaction=nonstopmode -halt-on-error manuscript.tex
