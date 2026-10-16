#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p artifacts logs
exec 9>artifacts/mirror.lock
flock -n 9 || exit 0
# Bounded mirror duration; no model execution, deletion, or Git staging.
for ((iteration=0; iteration<${MIRROR_ITERATIONS:-60}; iteration++)); do
  if bash scripts/sync.sh pull; then
    date -u +%Y-%m-%dT%H:%M:%SZ > artifacts/last-successful-mirror.txt
  else
    # Transport failure does not lose earlier checkpoints or terminate mirroring.
    date -u +%Y-%m-%dT%H:%M:%SZ >> logs/mirror-failures.log
  fi
  sleep 60
done
