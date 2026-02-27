FROM runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/hf_cache

WORKDIR /app

# System dependency: ffmpeg for audio format conversion
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Uninstall conflicting pre-installed torchvision, then install chatterbox-tts + runpod
RUN pip uninstall -y torchvision && \
    pip install --no-cache-dir chatterbox-tts runpod

# Pre-download model weights so cold starts are fast
RUN python -c "\
from chatterbox.tts import ChatterboxTTS; \
ChatterboxTTS.from_pretrained(device='cpu') \
"

# Create voice reference directory
RUN mkdir -p /app/voices

# Copy handler
COPY handler.py /app/handler.py

CMD ["python", "-u", "/app/handler.py"]
