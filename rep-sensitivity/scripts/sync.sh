#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
remote="${RUNPOD_HOST:-root@195.26.233.32}"
remote_dir="${RUNPOD_PROJECT:-/workspace/rep-sensitivity}"
port="${RUNPOD_PORT:-19997}"
key="${RUNPOD_KEY:-$HOME/.ssh/id_rsa}"
known="${RUNPOD_KNOWN_HOSTS:-/tmp/intellisys-runpod-known-hosts}"
transport="ssh -i $key -o IdentitiesOnly=yes -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=15 -o ServerAliveCountMax=3 -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$known -p $port"
case "${1:-pull}" in
  push-source)
    rsync -az -e "$transport" --exclude='.venv/' --exclude='artifacts/' --exclude='logs/' \
      --exclude='results/' --exclude='__pycache__/' --exclude='.git/' ./ "$remote:$remote_dir/" ;;
  pull)
    mkdir -p artifacts/runs records
    rsync -az -e "$transport" --exclude='*.partial' "$remote:$remote_dir/artifacts/runs/" artifacts/runs/
    # Local analyses and manuscript checks may be newer than the source snapshot
    # on a running pod. Do not replace these with older remote records.
    rsync -auz -e "$transport" "$remote:$remote_dir/records/" records/
    rsync -auz -e "$transport" --include='frozen/' --include='frozen/***' --exclude='*' "$remote:$remote_dir/configs/" configs/
    rsync -auz -e "$transport" "$remote:$remote_dir/results/" results/ ;;
  *) printf 'Usage: bash scripts/sync.sh push-source|pull\n' >&2; exit 2 ;;
esac
