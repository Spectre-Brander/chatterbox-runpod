FROM runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/hf_cache

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip uninstall -y torchvision && \
    pip install --no-cache-dir chatterbox-tts runpod

# Pre-download weights to cache (don't load model — just cache the files)
RUN python -c "\
import os; os.environ['TRANSFORMERS_VERBOSITY']='error'; \
from huggingface_hub import snapshot_download; \
snapshot_download('ResembleAI/chatterbox', cache_dir='/app/hf_cache'); \
print('Weights cached.') \
"

RUN mkdir -p /app/voices

COPY handler.py /app/handler.py

CMD ["python", "-u", "/app/handler.py"]
