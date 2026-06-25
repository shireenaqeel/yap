"""Retrieval-augmented answering. Retrieve from the user's own corpus, then
ask Groq's Llama-3.1-8B to answer in first person, grounded only in what was
retrieved.
"""

from __future__ import annotations

from . import config
from .embeddings import embed
from .storage import UserStore

SYSTEM_PROMPT = """You are the user's own inner voice, reflecting back to them.
Answer in the FIRST PERSON, as if you are the user speaking about themselves.
You may ONLY use the journal excerpts provided as context. If the excerpts do
not contain enough to answer, say so honestly ("I haven't written enough about
that yet") instead of inventing anything. Be warm, concrete, and specific —
quote or reference what was actually written. Never fabricate events.
"""


def _build_context(chunks: list[dict]) -> str:
    lines = []
    for c in chunks:
        tag = c.get("type", "entry")
        date = c.get("date", "")[:10]
        lines.append(f"[{tag} · {date}] {c['text']}")
    return "\n\n".join(lines)


def answer(store: UserStore, question: str, k: int = config.TOP_K) -> dict:
    """Return {'answer': str, 'sources': list[dict]}."""
    if not config.GROQ_API_KEY:
        return {
            "answer": "No GROQ_API_KEY configured. Add one to your .env "
            "(see .env.example) to enable answers.",
            "sources": [],
        }

    query_vec = embed([question])[0]
    sources = store.search(query_vec, k=k)
    if not sources:
        return {
            "answer": "I haven't written anything yet — yap a few entries "
            "first, then ask me about yourself.",
            "sources": [],
        }

    from groq import Groq

    client = Groq(api_key=config.GROQ_API_KEY)
    context = _build_context(sources)
    user_msg = (
        f"My journal excerpts:\n\n{context}\n\n"
        f"Question about myself: {question}"
    )

    resp = client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.4,
    )
    return {"answer": resp.choices[0].message.content, "sources": sources}
