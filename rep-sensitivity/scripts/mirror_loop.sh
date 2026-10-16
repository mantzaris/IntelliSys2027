#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p artifacts logs
exec 9>artifacts/mirror.lock
flock -n 9 || exit 0
# Bounded mirror duration; no model execution or deletion. The optional completion
# hook can commit generated essentials on main, as requested, without pushing.
for ((iteration=0; iteration<${MIRROR_ITERATIONS:-60}; iteration++)); do
  if bash scripts/sync.sh pull; then
    date -u +%Y-%m-%dT%H:%M:%SZ > artifacts/last-successful-mirror.txt
    if [[ -f scripts/finalize_local.py ]]; then
      completion_options=()
      if [[ "${FINALIZE_COMMIT:-0}" == 1 ]]; then completion_options+=(--commit); fi
      .venv/bin/python scripts/finalize_local.py "${completion_options[@]}" >> logs/local-finalization.log 2>&1 || true
    fi
    if [[ -f artifacts/review-package-commit.json && -f artifacts/runs/study-execution-v8/secondary_replay_and_live-complete.json ]]; then
      break
    fi
  else
    # Transport failure does not lose earlier checkpoints or terminate mirroring.
    date -u +%Y-%m-%dT%H:%M:%SZ >> logs/mirror-failures.log
  fi
  sleep 60
done
