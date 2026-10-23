#!/usr/bin/env bash
set -euo pipefail
PCC_REPORT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PCC_REPORT_ROOT"
export PYTHONPATH=src
.venv/bin/python -m pcc.package
.venv/bin/python analysis/exploratory_descriptives.py
bash scripts/build_paper.sh
