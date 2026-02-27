#!/bin/bash
set -e

export HF_HOME="${HF_HOME:-/runpod-volume/hf_cache}"
export PIP_CACHE_DIR="/runpod-volume/pip_cache"
mkdir -p "$HF_HOME" "$PIP_CACHE_DIR" /app/voices

# Install deps (cached on volume after first run)
if ! python -c "import runpod; import chatterbox" 2>/dev/null; then
    echo "[spectre-tts] Installing dependencies..."
    apt-get update && apt-get install -y --no-install-recommends ffmpeg 2>/dev/null || true
    pip install --cache-dir "$PIP_CACHE_DIR" chatterbox-tts runpod
    echo "[spectre-tts] Dependencies installed."
else
    echo "[spectre-tts] Dependencies already available."
    # Ensure ffmpeg is there
    which ffmpeg || (apt-get update && apt-get install -y --no-install-recommends ffmpeg 2>/dev/null || true)
fi

# Download handler from GitHub (use API for reliability)
echo "[spectre-tts] Fetching handler..."
curl -sL -H "Accept: application/vnd.github.raw" \
  https://api.github.com/repos/Spectre-Brander/chatterbox-runpod/contents/handler.py -o /app/handler.py

if [ ! -s /app/handler.py ]; then
    echo "[spectre-tts] ERROR: Failed to download handler.py"
    exit 1
fi

echo "[spectre-tts] Starting handler..."
cd /app && python -u handler.py
