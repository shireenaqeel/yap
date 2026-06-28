"""Proactive reflection prompts. Reads the user's recent yaps and asks Groq for
one short, probing question to nudge their next entry — so Yap feels like it
already knows them instead of waiting passively for input.
"""

from __future__ import annotations

import random

from . import config, patterns
from .storage import UserStore

# Used before there's anything written, or when no key is configured.
_FALLBACKS = [
    "What's been quietly taking up space in your mind lately?",
    "What did you feel today that you didn't say out loud?",
    "If you could tell yourself one thing a week ago, what would it be?",
    "What's something small that went better than you expected?",
]

_SYS = """You are a warm, perceptive journaling companion. Given a few of the
user's recent journal excerpts, write ONE short, open-ended question (max 25
words) that gently invites them to reflect deeper. Ground it in what they
actually wrote, but stay kind and specific. Address them as "you". Output ONLY
the question — no preamble, no quotation marks."""


def reflection_prompt(store: UserStore, days: int = 14, n: int = 6) -> str:
    """Return a single reflection question tailored to recent yaps."""
    chunks = [
        c for c in patterns.recent_chunks(store, days)
        if c.get("type") == "yap_entry"
    ]
    if not chunks or not config.GROQ_API_KEY:
        return random.choice(_FALLBACKS)

    blob = "\n".join(f"- {c['text']}" for c in chunks[-n:])

    from groq import Groq

    client = Groq(api_key=config.GROQ_API_KEY)
    resp = client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=[
            {"role": "system", "content": _SYS},
            {"role": "user", "content": f"My recent yaps:\n\n{blob}"},
        ],
        temperature=0.8,
    )
    return resp.choices[0].message.content.strip().strip('"')
