"""Text-to-speech read-back for spoken reflection. Uses the gTTS library
(Google Translate TTS) and returns MP3 bytes that Streamlit can play inline,
so the "Ask Yourself" answer can be heard in addition to read.
"""

from __future__ import annotations

import io

MAX_CHARS = 1200  # keep read-backs snappy and within sane request size


def speak(text: str, lang: str = "en") -> bytes:
    """Synthesize `text` to MP3 bytes."""
    from gtts import gTTS

    snippet = text.strip()[:MAX_CHARS]
    buf = io.BytesIO()
    gTTS(text=snippet, lang=lang).write_to_fp(buf)
    return buf.getvalue()
