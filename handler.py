"""
RunPod Serverless Handler for Chatterbox TTS (resemble-ai/chatterbox).

Loads the model once at cold start, then processes text-to-speech requests.
Returns base64-encoded audio in mp3, wav, or ogg format.
"""

import os
import io
import base64
import subprocess
import tempfile

import torch
import torchaudio
import runpod

# ---------------------------------------------------------------------------
# Cold start: load the model once when the worker boots
# ---------------------------------------------------------------------------
VOICE_REF_PATH = os.environ.get("VOICE_REF_PATH", "/app/voices/spectre-primary.wav")

print("Loading ChatterboxTTS model …")
from chatterbox.tts import ChatterboxTTS

MODEL = ChatterboxTTS.from_pretrained(device="cuda")
print("Model loaded.")

HAS_VOICE_REF = os.path.isfile(VOICE_REF_PATH)
if HAS_VOICE_REF:
    print(f"Voice reference found: {VOICE_REF_PATH}")
else:
    print(f"No voice reference at {VOICE_REF_PATH} — using built-in voice.")


def _wav_tensor_to_bytes(wav: torch.Tensor, sr: int) -> bytes:
    """Serialize a torchaudio tensor to an in-memory WAV."""
    buf = io.BytesIO()
    torchaudio.save(buf, wav.cpu(), sr, format="wav")
    buf.seek(0)
    return buf.read()


def _convert_audio(wav_bytes: bytes, output_format: str) -> bytes:
    """Convert raw WAV bytes to the requested format using ffmpeg."""
    if output_format == "wav":
        return wav_bytes

    fmt_args = {
        "mp3":  ["-f", "mp3", "-codec:a", "libmp3lame", "-q:a", "2"],
        "ogg":  ["-f", "ogg", "-codec:a", "libopus", "-b:a", "96k"],
    }

    if output_format not in fmt_args:
        raise ValueError(f"Unsupported output format: {output_format!r}")

    cmd = [
        "ffmpeg", "-y",
        "-f", "wav", "-i", "pipe:0",
        *fmt_args[output_format],
        "pipe:1",
    ]

    proc = subprocess.run(
        cmd,
        input=wav_bytes,
        capture_output=True,
    )

    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {proc.stderr.decode()}")

    return proc.stdout


def handler(job: dict) -> dict:
    """RunPod serverless handler — text-to-speech via Chatterbox."""
    job_input = job["input"]

    text = job_input.get("text")
    if not text:
        return {"error": "Missing required field: 'text'"}

    output_format = job_input.get("output_format", "mp3").lower()
    if output_format not in ("mp3", "wav", "ogg"):
        return {"error": f"Unsupported output_format: {output_format!r}. Use mp3, wav, or ogg."}

    # Optional generation parameters
    exaggeration = job_input.get("exaggeration", 0.5)
    cfg_weight = job_input.get("cfg_weight", 0.5)
    temperature = job_input.get("temperature", 0.8)

    # Generate speech
    generate_kwargs = dict(
        text=text,
        exaggeration=exaggeration,
        cfg_weight=cfg_weight,
        temperature=temperature,
    )
    if HAS_VOICE_REF:
        generate_kwargs["audio_prompt_path"] = VOICE_REF_PATH

    wav = MODEL.generate(**generate_kwargs)

    # Convert to requested format
    wav_bytes = _wav_tensor_to_bytes(wav, MODEL.sr)
    audio_bytes = _convert_audio(wav_bytes, output_format)
    audio_b64 = base64.b64encode(audio_bytes).decode("ascii")

    return {
        "audio_base64": audio_b64,
        "format": output_format,
    }


runpod.serverless.start({"handler": handler})
