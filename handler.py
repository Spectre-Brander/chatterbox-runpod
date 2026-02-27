"""
RunPod Serverless Handler for Chatterbox TTS.
Lazy-loads model on first request to avoid init timeout.
"""

import os
import io
import base64
import subprocess
import torch
import torchaudio
import runpod

VOICE_REF_PATH = os.environ.get("VOICE_REF_PATH", "/app/voices/spectre-primary.wav")
MODEL = None


def get_model():
    global MODEL
    if MODEL is None:
        print("[spectre-tts] Loading ChatterboxTTS model...", flush=True)
        from chatterbox.tts import ChatterboxTTS
        MODEL = ChatterboxTTS.from_pretrained(device="cuda")
        print("[spectre-tts] Model loaded.", flush=True)
    return MODEL


def _wav_to_bytes(wav, sr):
    buf = io.BytesIO()
    torchaudio.save(buf, wav.cpu(), sr, format="wav")
    buf.seek(0)
    return buf.read()


def _convert(wav_bytes, fmt):
    if fmt == "wav":
        return wav_bytes
    args = {
        "mp3": ["-f", "mp3", "-codec:a", "libmp3lame", "-q:a", "2"],
        "ogg": ["-f", "ogg", "-codec:a", "libopus", "-b:a", "96k"],
    }
    if fmt not in args:
        raise ValueError(f"Unsupported format: {fmt}")
    proc = subprocess.run(
        ["ffmpeg", "-y", "-f", "wav", "-i", "pipe:0"] + args[fmt] + ["pipe:1"],
        input=wav_bytes, capture_output=True
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {proc.stderr.decode()}")
    return proc.stdout


def handler(job):
    inp = job["input"]
    text = inp.get("text")
    if not text:
        return {"error": "Missing 'text'"}

    fmt = inp.get("output_format", "mp3").lower()
    if fmt not in ("mp3", "wav", "ogg"):
        return {"error": f"Unsupported format: {fmt}"}

    model = get_model()

    kwargs = {"text": text}
    if os.path.isfile(VOICE_REF_PATH):
        kwargs["audio_prompt_path"] = VOICE_REF_PATH

    for k in ("exaggeration", "cfg_weight", "temperature"):
        if k in inp:
            kwargs[k] = inp[k]

    wav = model.generate(**kwargs)
    wav_bytes = _wav_to_bytes(wav, model.sr)
    audio_bytes = _convert(wav_bytes, fmt)

    return {
        "audio_base64": base64.b64encode(audio_bytes).decode("ascii"),
        "format": fmt,
    }


runpod.serverless.start({"handler": handler})
