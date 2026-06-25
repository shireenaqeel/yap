"""Lightweight pattern analysis for the recap view. No heavy ML — keyword and
frequency stats over recent entries are enough for the MVP.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timedelta, timezone

from .storage import UserStore


def category_counts(chunks: list[dict]) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    for c in chunks:
        cat = c.get("category")
        if cat:
            counter[cat] += 1
    return counter.most_common()

# Common words we don't want surfacing as "topics".
STOPWORDS = set(
    """a an and the of to in is it i im i'm me my we you your he she they them
    this that these those for on at by with as but or so if then than too very
    just really also been being am are was were be do does did have has had will
    would can could should may might must not no yes get got go going went make
    made about into over under out up down off again once here there when where
    why how what who whom which while because about from like one two day today
    feel felt feeling thing things lot still even much more most some any all""".split()
)

WORD_RE = re.compile(r"[a-zA-Z']{3,}")


def _parse_date(record: dict) -> datetime | None:
    raw = record.get("date")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def recent_chunks(store: UserStore, days: int = 30) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    out = []
    for c in store.all_chunks():
        d = _parse_date(c)
        if d is None or d >= cutoff:
            out.append(c)
    return out


def top_keywords(chunks: list[dict], n: int = 12) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    for c in chunks:
        for word in WORD_RE.findall(c.get("text", "").lower()):
            if word not in STOPWORDS:
                counter[word] += 1
    return counter.most_common(n)


def activity_by_day(chunks: list[dict]) -> list[tuple[str, int]]:
    """Entries-per-day, sorted by date, for a simple trend line."""
    counter: Counter[str] = Counter()
    for c in chunks:
        d = _parse_date(c)
        if d:
            counter[d.date().isoformat()] += 1
    return sorted(counter.items())


def summary(store: UserStore, days: int = 30) -> dict:
    chunks = recent_chunks(store, days)
    yaps = sum(1 for c in chunks if c.get("type") == "yap_entry")
    docs = sum(1 for c in chunks if c.get("type") == "document")
    return {
        "total_chunks": len(chunks),
        "yap_chunks": yaps,
        "doc_chunks": docs,
        "keywords": top_keywords(chunks),
        "activity": activity_by_day(chunks),
        "categories": category_counts(chunks),
        "days": days,
    }
