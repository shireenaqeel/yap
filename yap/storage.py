"""Per-user storage. The hard rule from the brief: one user_id, one folder,
nothing ever reads or writes across folders.

Each user owns exactly two files, kept in lockstep:
    data/users/{user_id}/faiss_index.bin   -> vectors only
    data/users/{user_id}/chunks.jsonl      -> id -> original text + metadata
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import faiss
import numpy as np

from . import config


def _safe_user_id(user_id: str) -> str:
    """Reduce an arbitrary typed name to a single safe path segment.

    This is the guard that makes cross-folder access impossible: no slashes,
    no '..', no drive letters can survive, so a user_id can only ever resolve
    to one direct child of DATA_DIR.
    """
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", user_id.strip()).strip("_")
    if not cleaned:
        raise ValueError("user_id must contain at least one usable character")
    return cleaned.lower()


class UserStore:
    """Owns one user's FAISS index + chunk store. Never touches anyone else."""

    def __init__(self, user_id: str):
        self.user_id = _safe_user_id(user_id)
        self.dir = (config.DATA_DIR / self.user_id).resolve()

        # Defence in depth: the resolved path must stay inside DATA_DIR.
        root = config.DATA_DIR.resolve()
        if root not in self.dir.parents and self.dir != root:
            raise ValueError("resolved user path escaped the data root")

        self.dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.dir / "faiss_index.bin"
        self.chunks_path = self.dir / "chunks.jsonl"

        self._index = self._load_index()

    # ---- index lifecycle -------------------------------------------------
    def _load_index(self) -> faiss.Index:
        if self.index_path.exists():
            return faiss.read_index(str(self.index_path))
        return faiss.IndexFlatIP(config.EMBED_DIM)

    def _save_index(self) -> None:
        faiss.write_index(self._index, str(self.index_path))

    @property
    def size(self) -> int:
        return self._index.ntotal

    # ---- writes ----------------------------------------------------------
    def add(self, chunks: list[str], vectors: np.ndarray, metadata: dict) -> int:
        """Append chunks (text) and their vectors atomically-ish.

        `metadata` is shared by every chunk in this call (e.g. one yap entry
        or one PDF). Returns the number of chunks added.
        """
        if not chunks:
            return 0
        if vectors.shape[0] != len(chunks):
            raise ValueError("vectors and chunks length mismatch")

        start_id = self._index.ntotal
        self._index.add(vectors)

        with self.chunks_path.open("a", encoding="utf-8") as f:
            for offset, text in enumerate(chunks):
                record = {"id": start_id + offset, "text": text, **metadata}
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        self._save_index()
        return len(chunks)

    # ---- reads -----------------------------------------------------------
    def all_chunks(self) -> list[dict]:
        if not self.chunks_path.exists():
            return []
        with self.chunks_path.open(encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def search(self, query_vec: np.ndarray, k: int = config.TOP_K) -> list[dict]:
        """Return the top-k chunk records for a single query vector."""
        if self._index.ntotal == 0:
            return []
        k = min(k, self._index.ntotal)
        scores, ids = self._index.search(query_vec.reshape(1, -1), k)

        by_id = {c["id"]: c for c in self.all_chunks()}
        results = []
        for score, idx in zip(scores[0], ids[0]):
            if idx < 0:
                continue
            chunk = by_id.get(int(idx))
            if chunk:
                results.append({**chunk, "score": float(score)})
        return results
