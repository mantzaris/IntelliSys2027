#!/usr/bin/env bash
set -euo pipefail
# SSH endpoint is supplied through environment variables; never store credentials.
: "${PCC_SSH_HOST:?set PCC_SSH_HOST}"
: "${PCC_SSH_PORT:?set PCC_SSH_PORT}"
PCC_SSH_KEY="${PCC_SSH_KEY:-$HOME/.ssh/id_rsa}"
PCC_REMOTE_DIR="${PCC_REMOTE_DIR:-/workspace/dualingCharacters}"
PCC_KNOWN_HOSTS="${PCC_KNOWN_HOSTS:-/tmp/intellisys-runpod-known-hosts}"
PCC_LOCAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
export RSYNC_RSH="ssh -F /dev/null -i $PCC_SSH_KEY -p $PCC_SSH_PORT -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$PCC_KNOWN_HOSTS"
case "${1:-pull}" in
  push)
    rsync -az --exclude='.venv*' --exclude='__pycache__' --exclude='.pytest_cache' \
      --exclude='artifacts' --exclude='data/generated' --exclude='data/external' \
      --exclude='literature/cache' "$PCC_LOCAL_DIR/" "root@$PCC_SSH_HOST:$PCC_REMOTE_DIR/"
    ;;
  pull)
    mkdir -p "$PCC_LOCAL_DIR/artifacts"
    rsync -az --exclude='hf-cache' --exclude='*.tmp' \
      "root@$PCC_SSH_HOST:$PCC_REMOTE_DIR/artifacts/" "$PCC_LOCAL_DIR/artifacts/"
    ;;
  *) exit 2 ;;
esac
