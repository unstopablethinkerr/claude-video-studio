#!/usr/bin/env bash
# Collects versions and diagnostics into debug-report.zip so you can share it
# (for example, upload it to the GitHub repo's issues). Never includes API keys.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/debug-report"
rm -rf "$OUT" && mkdir -p "$OUT"
export PATH="$HOME/.local/bin:$PATH"
HF="npx --yes hyperframes@0.9.19"

{
  echo "date: $(date -u)"
  echo "os: $(uname -a)"
  echo "node: $(node -v 2>&1)"
  echo "npm: $(npm -v 2>&1)"
  echo "uv: $(uv --version 2>&1)"
  echo "jl: $(jl --version 2>&1)"
  echo "ffmpeg: $(ffmpeg -version 2>&1 | head -1)"
  echo "python3: $(python3 --version 2>&1)"
  echo "claude: $(claude --version 2>&1)"
} > "$OUT/versions.txt"

$HF doctor > "$OUT/hyperframes-doctor.txt" 2>&1
$HF lint projects/starter > "$OUT/lint-starter.txt" 2>&1
jl gpus > "$OUT/jl-gpus.txt" 2>&1 || true
jl status > "$OUT/jl-status.txt" 2>&1 || true
ls -la "$ROOT" "$ROOT/projects" "$ROOT/raws" "$ROOT/outputs" > "$OUT/folders.txt" 2>&1

# Redact anything that looks like a token before sharing.
grep -rlE "JL_API_KEY|token|api[_-]?key" "$OUT" >/dev/null 2>&1 && \
  sed -i -E 's/(JL_API_KEY|token|api[_-]?key)[^[:space:]]*/\1=REDACTED/Ig' "$OUT"/*.txt

ZIP="$ROOT/debug-report.zip"
rm -f "$ZIP"
(cd "$ROOT" && zip -qr "$ZIP" debug-report) 2>/dev/null || tar -czf "$ZIP.tgz" -C "$ROOT" debug-report
rm -rf "$OUT"
echo "Created: $ZIP (attach it to a GitHub issue or send it to the maintainer)"
