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

# Python dependencies — install chatterbox-tts (brings torch, torchaudio, etc.)
# Pin runpod separately since it's not a chatterbox dependency
RUN pip install --no-cache-dir \
    chatterbox-tts \
    runpod

# Pre-download model weights so cold starts don't require a HuggingFace download.
# This bakes ~2 GB of weights into the image layer.
RUN python -c "\
from chatterbox.tts import ChatterboxTTS; \
ChatterboxTTS.from_pretrained(device='cpu') \
"

# Create voice reference directory (users can bake a WAV in or mount one)
RUN mkdir -p /app/voices

# Copy handler last (changes most often → best Docker layer caching)
COPY handler.py /app/handler.py

CMD ["python", "-u", "/app/handler.py"]
