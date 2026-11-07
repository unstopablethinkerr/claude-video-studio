#!/usr/bin/env bash
# One-time local setup: Node 22+, uv, Jarvis Labs CLI, HyperFrames skills, browser, folders.
# Safe to re-run.
set -uo pipefail

HF="npx --yes hyperframes@0.9.19"
fail() { echo "ERROR: $*" >&2; exit 1; }
warn() { echo "WARNING: $*" >&2; }

echo "== Claude Video Studio: local setup =="

command -v node >/dev/null 2>&1 || fail "Node.js is missing. Install Node 22+ from https://nodejs.org and rerun."
node -e 'process.exit(parseInt(process.versions.node, 10) >= 22 ? 0 : 1)' || fail "Node $(node -v) found, but HyperFrames needs Node 22+."
command -v npx >/dev/null 2>&1 || fail "npx not found. Reinstall Node.js 22+ (npm is bundled)."

if ! command -v uv >/dev/null 2>&1; then
  echo "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh || fail "Could not install uv. Install it from https://docs.astral.sh/uv/"
fi
export PATH="$HOME/.local/bin:$PATH"

echo "Installing / upgrading the Jarvis Labs CLI..."
uv tool install jarvislabs >/dev/null 2>&1 || uv tool upgrade jarvislabs >/dev/null 2>&1 || warn "Jarvis CLI install failed. Run: uv tool install jarvislabs"

echo "Installing HyperFrames skills for Claude Code..."
npx --yes skills add heygen-com/hyperframes </dev/null || warn "Skill install failed. Retry: npx skills add heygen-com/hyperframes"

echo "Checking the headless browser HyperFrames needs for rendering..."
if ! $HF browser ensure; then
  warn "Could not install the browser automatically. Install Google Chrome, then run:"
  warn "  export HYPERFRAMES_BROWSER_PATH=/path/to/chrome"
fi

echo "Running HyperFrames doctor (optional items may show as missing)..."
$HF doctor || true

mkdir -p raws outputs projects

cat <<'MSG'

Setup finished. Next steps:
  1. Run `jl setup` and paste your Jarvis Labs API token. Choose Claude Code when asked.
  2. Run `jl status` to check your balance (only needed for cloud work).
  3. Put footage into raws/ and open Claude Code in this folder with `claude`.
  4. Test the starter: npx --yes hyperframes@0.9.19 lint projects/starter

If something failed, run: bash scripts/collect-debug.sh   and share the zip it creates.
MSG
