# Reproduce this bounded study

From `dualingCharacters/`, using the repository's pinned local Python environment:

```bash
PYTHONPATH=src:. .venv/bin/python -m unittest discover -s supplements/generalization_edge_cases_009/tests -v
PYTHONPATH=src:. .venv/bin/python -m supplements.generalization_edge_cases_009.protection
```

For immediate full-dialogue access without Python, run from this supplement directory:

```bash
gzip -dc evidence/FULL_DIALOGUES.html.gz > FULL_DIALOGUES.html
```

The committed compact archive `evidence/edge009_records.tar.gz` contains the complete new development/research generations, prompts, actor observations, configs, statuses, token/batch logs and timing outputs. It excludes model weights, old bulk runs and connection credentials. Extraction is offline:

```bash
mkdir -p /tmp/edge009-reproduction
tar -xzf supplements/generalization_edge_cases_009/evidence/edge009_records.tar.gz -C /tmp/edge009-reproduction
PYTHONPATH=src:. .venv/bin/python -m supplements.generalization_edge_cases_009.analysis --run-root /tmp/edge009-reproduction/runs
PYTHONPATH=src:. .venv/bin/python -m supplements.generalization_edge_cases_009.report --run-root /tmp/edge009-reproduction/runs
PYTHONPATH=src:. .venv/bin/python -m supplements.generalization_edge_cases_009.dialogues --run-root /tmp/edge009-reproduction/runs
PYTHONPATH=src:. .venv/bin/python -m supplements.generalization_edge_cases_009.exposure --run-root /tmp/edge009-reproduction/runs
PYTHONPATH=src:. .venv/bin/python -m supplements.generalization_edge_cases_009.trajectory_details --run-root /tmp/edge009-reproduction/runs
PYTHONPATH=src:. .venv/bin/python -m supplements.generalization_edge_cases_009.replay_analysis --run-root /tmp/edge009-reproduction/runs
PYTHONPATH=src:. .venv/bin/python -m supplements.generalization_edge_cases_009.verify --run-root /tmp/edge009-reproduction/runs
```

NumPy and Matplotlib are already present in the pinned project environment. Unit tests use synthetic software fixtures only. Integration verification requires the committed evidence archive; missing evidence is a prerequisite failure, never substituted with synthetic results. HTML is self-contained and has no external scripts/assets. `FULL_DIALOGUES.html` retains actual order, sources, prompts, delivered prefixes and complete generated text. Source locators use archive-relative `runs/<run>/<condition>[_characters].jsonl#L<n>`; hashes are in the provenance manifest.

No new inference is scheduled by these commands. The admissions are historical execution specifications, not permission to rerun them. Reusing run IDs is forbidden by the native ledger. The stage009 ownership handoff is closed before final handoff; any future study needs a new authorization and budget gate. Native campaign recovery information remains in the private `artifacts/generalization_edge_cases_009/` handoff records and the public session report.
