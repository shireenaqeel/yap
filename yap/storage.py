"""Per-user storage backed by Postgres + pgvector. Every query is scoped by
user_id, so one account can never read another's entries.
"""

from __future__ import annotations

import numpy as np

from . import config
from .db import get_conn


class UserStore:
    """Owns one user's rows in the shared `entries` table."""

    def __init__(self, user_id: int):
        self.user_id = int(user_id)

    @property
    def size(self) -> int:
        with get_conn().cursor() as cur:
            cur.execute(
                "select count(*) from entries where user_id = %s", (self.user_id,)
            )
            return cur.fetchone()[0]

    # ---- writes ----------------------------------------------------------
    def add(self, chunks: list[str], vectors: np.ndarray, metadata: dict) -> int:
        """Insert chunks + vectors for this user. `metadata` carries
        type / category / source shared by every chunk in the call."""
        if not chunks:
            return 0
        if vectors.shape[0] != len(chunks):
            raise ValueError("vectors and chunks length mismatch")

        rows = [
            (
                self.user_id,
                text,
                vectors[i],
                metadata.get("type", "yap_entry"),
                metadata.get("category"),
                metadata.get("source"),
            )
            for i, text in enumerate(chunks)
        ]
        with get_conn().cursor() as cur:
            cur.executemany(
                "insert into entries "
                "(user_id, text, embedding, type, category, source) "
                "values (%s, %s, %s, %s, %s, %s)",
                rows,
            )
        return len(chunks)

    # ---- reads -----------------------------------------------------------
    def all_chunks(self) -> list[dict]:
        with get_conn().cursor() as cur:
            cur.execute(
                "select text, type, category, source, created_at "
                "from entries where user_id = %s order by created_at",
                (self.user_id,),
            )
            return [self._row(r) for r in cur.fetchall()]

    def search(self, query_vec: np.ndarray, k: int = config.TOP_K) -> list[dict]:
        """Top-k most similar chunks for this user (cosine via pgvector)."""
        with get_conn().cursor() as cur:
            cur.execute(
                "select text, type, category, source, created_at, "
                "1 - (embedding <=> %s) as score "
                "from entries where user_id = %s "
                "order by embedding <=> %s limit %s",
                (query_vec, self.user_id, query_vec, k),
            )
            out = []
            for r in cur.fetchall():
                d = self._row(r)
                d["score"] = float(r[5])
                out.append(d)
            return out

    def list_entries(self, limit: int = 300) -> list[dict]:
        """Most-recent-first entries with their ids (for the journal view)."""
        with get_conn().cursor() as cur:
            cur.execute(
                "select id, text, type, category, source, created_at "
                "from entries where user_id = %s order by created_at desc limit %s",
                (self.user_id, limit),
            )
            out = []
            for r in cur.fetchall():
                d = self._row(r[1:])
                d["id"] = r[0]
                out.append(d)
            return out

    # ---- deletes ---------------------------------------------------------
    def delete(self, entry_id: int) -> None:
        """Delete one entry — scoped by user_id so you can only delete your own."""
        with get_conn().cursor() as cur:
            cur.execute(
                "delete from entries where id = %s and user_id = %s",
                (int(entry_id), self.user_id),
            )

    def clear(self) -> int:
        """Delete every entry for this user. Returns how many chunks were removed."""
        with get_conn().cursor() as cur:
            cur.execute("delete from entries where user_id = %s", (self.user_id,))
            return cur.rowcount

    def delete_by_type(self, type_: str) -> None:
        """Delete all of this user's entries of a given type (e.g. 'profile'),
        so re-saving doesn't pile up duplicates."""
        with get_conn().cursor() as cur:
            cur.execute(
                "delete from entries where user_id = %s and type = %s",
                (self.user_id, type_),
            )

    @staticmethod
    def _row(r) -> dict:
        return {
            "text": r[0],
            "type": r[1],
            "category": r[2],
            "source": r[3],
            "date": r[4].isoformat() if r[4] else "",
        }
