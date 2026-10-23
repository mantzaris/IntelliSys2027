#!/usr/bin/env bash
set -euo pipefail
PCC_REPORT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PCC_REPORT_ROOT"
export PYTHONPATH=src
.venv/bin/python analysis/audit_artifacts.py
.venv/bin/python analysis/audit_lineage.py
.venv/bin/python analysis/design_coverage.py
.venv/bin/python -m pcc.package
.venv/bin/python analysis/serialization_report.py
.venv/bin/python analysis/exploratory_descriptives.py
.venv/bin/python analysis/retrieval_descriptives.py
.venv/bin/python analysis/summarize_unseen_profiles.py
.venv/bin/python analysis/clear_empty_exports.py
.venv/bin/python analysis/publication_tables.py
.venv/bin/python analysis/human_review.py
bash scripts/build_paper.sh
