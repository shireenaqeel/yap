"""Personality Wrapped — a Spotify-Wrapped-style AI recap of the user's recent
yaps. Groq reads the entries and writes a short, punchy personality summary
that changes as the user writes more.
"""

from __future__ import annotations

from collections import Counter

from . import config, patterns
from .storage import UserStore

WRAPPED_PROMPT = """You are writing a fun, warm "Personality Wrapped" — like
Spotify Wrapped, but for someone's journal. You are given their journal entries
for a period. Produce a short, punchy recap with these sections, using markdown:

### 🎬 Your {period} in a sentence
One vivid sentence capturing the overall vibe.

### 🔥 Your top themes
3-5 bullets naming what they kept circling back to (be specific to the text).

### 🌡️ Mood arc
1-2 sentences on the emotional shape of the period.

### 🧬 Your personality this {period}
A 2-3 sentence "personality type" blurb, fun but kind and grounded ONLY in what
they actually wrote. Give it a catchy 2-4 word title in bold.

### ✨ One thing to notice
A single gentle, useful observation about a pattern they might not see.

Rules: warm, specific, second person ("you"). Use only what's in the entries —
never invent events. Keep the whole thing tight."""


def _entries_blob(chunks: list[dict], limit: int = 60) -> str:
    lines = []
    for c in chunks[-limit:]:
        cat = f" [{c['category']}]" if c.get("category") else ""
        date = c.get("date", "")[:10]
        lines.append(f"- ({date}){cat} {c['text']}")
    return "\n".join(lines)


def generate(store: UserStore, days: int = 30) -> dict:
    """Return {'recap': markdown, 'stats': {...}} for the last `days`."""
    period = "month" if days > 14 else "week"
    chunks = [c for c in patterns.recent_chunks(store, days)
              if c.get("type") == "yap_entry"]

    cats = Counter(c["category"] for c in chunks if c.get("category"))
    stats = {
        "entries": len(chunks),
        "top_category": cats.most_common(1)[0][0] if cats else None,
        "categories": cats.most_common(),
        "keywords": patterns.top_keywords(chunks, 8),
        "period": period,
    }

    if len(chunks) < 2:
        return {
            "recap": "You need at least a couple of yaps in this period before "
            "I can wrap you up. Go yap a few things and come back!",
            "stats": stats,
        }
    if not config.GROQ_API_KEY:
        return {
            "recap": "Add a GROQ_API_KEY to generate your AI Wrapped.",
            "stats": stats,
        }

    from groq import Groq

    client = Groq(api_key=config.GROQ_API_KEY)
    prompt = WRAPPED_PROMPT.replace("{period}", period)
    resp = client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"My journal for the last {days} days:\n\n"
             f"{_entries_blob(chunks)}"},
        ],
        temperature=0.7,
    )
    return {"recap": resp.choices[0].message.content, "stats": stats}
