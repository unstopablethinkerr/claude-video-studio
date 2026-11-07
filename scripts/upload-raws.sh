#!/usr/bin/env bash
# Upload local raws/ and projects/ to a Jarvis Labs instance under /home/work.
# Usage: bash scripts/upload-raws.sh <machine_id>
set -euo pipefail
MACHINE_ID="${1:?Usage: upload-raws.sh <machine_id>}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REMOTE=/home/work
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

jl exec "$MACHINE_ID" -- mkdir -p "$REMOTE"

# Projects: pack as one archive (skips node_modules and renders), then unpack remotely.
tar -czf "$TMP/projects.tgz" --exclude=node_modules --exclude=renders -C "$ROOT" projects
jl upload "$MACHINE_ID" "$TMP/projects.tgz" "$REMOTE/projects.tgz"
jl exec "$MACHINE_ID" -- tar -xzf "$REMOTE/projects.tgz" -C "$REMOTE"

# Raws: upload the folder into the remote parent directory, so it lands at $REMOTE/raws.
if [ -d "$ROOT/raws" ] && [ -n "$(ls -A "$ROOT/raws" 2>/dev/null)" ]; then
  jl upload "$MACHINE_ID" "$ROOT/raws" "$REMOTE"
else
  echo "No files in raws/ yet. Skipping raw upload."
fi
echo "Upload finished. Remote folder: $REMOTE"
