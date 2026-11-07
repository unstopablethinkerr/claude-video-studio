#!/usr/bin/env bash
# Bulk job on a Jarvis Labs instance:
#   upload -> bootstrap -> transcribe -> render every project -> download outputs.
# Usage: bash scripts/cloud-render.sh <machine_id>
# Remote shell commands use `jl exec <id> -- <command>`, which runs them via `sh -lc`.
set -euo pipefail
MACHINE_ID="${1:?Usage: cloud-render.sh <machine_id>}"
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
REMOTE=/home/work
HF_CMD="export HYPERFRAMES_BROWSER_PATH=/usr/bin/google-chrome-stable; cd $REMOTE; npx --yes hyperframes@0.9.19"

cd "$ROOT"

echo "[1/7] Checking instance $MACHINE_ID"
jl get "$MACHINE_ID" >/dev/null

echo "[2/7] Uploading raws and projects"
bash "$HERE/upload-raws.sh" "$MACHINE_ID"

echo "[3/7] Bootstrapping instance (Node 22, ffmpeg, Chrome, faster-whisper)"
jl upload "$MACHINE_ID" "$HERE/remote-bootstrap.sh" "$REMOTE/remote-bootstrap.sh"
jl exec "$MACHINE_ID" -- bash "$REMOTE/remote-bootstrap.sh"

echo "[4/7] Transcribing raws on the instance"
jl upload "$MACHINE_ID" "$HERE/transcribe.py" "$REMOTE/transcribe.py"
if [ -n "$(ls -A raws 2>/dev/null)" ]; then
  jl exec "$MACHINE_ID" -- bash -c "source \$HOME/whisper-env/bin/activate && cd $REMOTE && mkdir -p outputs/subs && python3 transcribe.py raws/ --out outputs/subs"
else
  echo "No raws to transcribe."
fi

echo "[5/7] Rendering projects"
rendered=0
for dir in projects/*/; do
  name="$(basename "$dir")"
  [ -f "$dir/index.html" ] || { echo "skip $name (no index.html)"; continue; }
  echo "  rendering $name"
  jl exec "$MACHINE_ID" -- bash -c "$HF_CMD render projects/$name -o outputs/$name.mp4"
  rendered=$((rendered + 1))
done
echo "  rendered $rendered project(s)"

echo "[6/7] Packing outputs on the instance and downloading"
jl exec "$MACHINE_ID" -- bash -c "cd $REMOTE && mkdir -p outputs && tar -czf outputs.tgz outputs"
jl download "$MACHINE_ID" "$REMOTE/outputs.tgz" "$ROOT/outputs.tgz"
if [ ! -s "$ROOT/outputs.tgz" ]; then
  echo "ERROR: download failed, outputs.tgz is missing. Outputs stay on the instance." >&2
  echo "Retry the download with: jl download $MACHINE_ID $REMOTE/outputs.tgz ./outputs.tgz" >&2
  exit 1
fi
tar -xzf "$ROOT/outputs.tgz" -C "$ROOT"
rm -f "$ROOT/outputs.tgz"

echo "[7/7] Done. Outputs are in outputs/."
echo "Stop compute billing when finished: jl pause $MACHINE_ID"
