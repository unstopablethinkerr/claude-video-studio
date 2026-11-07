#!/usr/bin/env bash
# Runs ON the Jarvis instance (Ubuntu/Debian, x86_64). Installs Node 22, ffmpeg,
# Google Chrome (for HyperFrames rendering), and faster-whisper. Safe to re-run.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

apt-get update -y
apt-get install -y ffmpeg curl ca-certificates gnupg python3-venv python3-pip

if ! command -v node >/dev/null 2>&1 || ! node -e 'process.exit(parseInt(process.versions.node,10)>=22?0:1)'; then
  curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
  apt-get install -y nodejs
fi

if ! command -v google-chrome-stable >/dev/null 2>&1; then
  curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg
  echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
  apt-get update -y
  apt-get install -y google-chrome-stable
fi

if [ ! -d "$HOME/whisper-env" ]; then
  python3 -m venv "$HOME/whisper-env"
fi
"$HOME/whisper-env/bin/pip" install -q --upgrade pip
"$HOME/whisper-env/bin/pip" install -q faster-whisper

echo "Node: $(node -v)  ffmpeg: $(ffmpeg -version | head -1 | cut -d' ' -f1-3)  Chrome: $(google-chrome-stable --version)"
echo "Bootstrap complete."
