#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Bounded mirror duration; no model execution, deletion, or Git staging.
for ((iteration=0; iteration<${MIRROR_ITERATIONS:-60}; iteration++)); do
  bash scripts/sync.sh pull
  sleep 60
done
