#!/bin/bash
set -e

export HF_HOME="${HF_HOME:-/runpod-volume/hf_cache}"
export PIP_CACHE_DIR="/runpod-volume/pip_cache"
mkdir -p "$HF_HOME" "$PIP_CACHE_DIR" /app/voices

# Install deps (cached on volume after first run)
if [ ! -f /runpod-volume/.deps_installed ]; then
    echo "[spectre-tts] Installing dependencies..."
    apt-get update && apt-get install -y --no-install-recommends ffmpeg
    pip install --cache-dir "$PIP_CACHE_DIR" chatterbox-tts runpod
    touch /runpod-volume/.deps_installed
    echo "[spectre-tts] Dependencies installed."
else
    echo "[spectre-tts] Dependencies already installed, reinstalling packages from cache..."
    pip install --cache-dir "$PIP_CACHE_DIR" chatterbox-tts runpod
fi

# Download handler from GitHub
echo "[spectre-tts] Fetching handler..."
curl -sL https://raw.githubusercontent.com/Spectre-Brander/chatterbox-runpod/main/handler.py -o /app/handler.py

echo "[spectre-tts] Starting handler..."
cd /app && python -u handler.py
