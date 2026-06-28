"""Speech-to-text for voice yapping. Uses Groq's hosted Whisper, so it reuses
the same GROQ_API_KEY as answering/Wrapped — no extra provider or model download.
"""

from __future__ import annotations

from . import config


def transcribe(audio_bytes: bytes, filename: str = "yap.wav") -> str:
    """Transcribe recorded audio to text. Raises RuntimeError if no key is set."""
    if not config.GROQ_API_KEY:
        raise RuntimeError("No GROQ_API_KEY configured — voice input needs it.")

    from groq import Groq

    client = Groq(api_key=config.GROQ_API_KEY)
    resp = client.audio.transcriptions.create(
        file=(filename, audio_bytes),
        model=config.GROQ_WHISPER_MODEL,
    )
    return resp.text.strip()
