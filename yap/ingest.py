"""Ingest pipeline: extract -> chunk -> embed -> store.

Both input paths (typed yap entries and uploaded PDFs) flow through the exact
same chunk/embed/store steps. They differ only in the metadata tag they carry.
"""

from __future__ import annotations

from datetime import datetime, timezone

from . import config
from .embeddings import embed
from .storage import UserStore


def chunk_text(text: str) -> list[str]:
    """Split text into overlapping character windows on sentence-ish breaks."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= config.CHUNK_SIZE:
        return [text]

    chunks: list[str] = []
    start = 0
    step = config.CHUNK_SIZE - config.CHUNK_OVERLAP
    while start < len(text):
        end = start + config.CHUNK_SIZE
        window = text[start:end]
        # Prefer to break at the last sentence boundary inside the window.
        if end < len(text):
            for sep in (". ", "\n", "! ", "? "):
                cut = window.rfind(sep)
                if cut > config.CHUNK_SIZE // 2:
                    window = window[: cut + len(sep)]
                    break
        chunks.append(window.strip())
        start += max(len(window) - config.CHUNK_OVERLAP, step)
    return [c for c in chunks if c]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ingest_text(store: UserStore, text: str) -> int:
    """Ingest a typed journal entry. Returns chunks added."""
    chunks = chunk_text(text)
    if not chunks:
        return 0
    vectors = embed(chunks)
    metadata = {"type": "yap_entry", "source": "typed", "date": _now_iso()}
    return store.add(chunks, vectors, metadata)


def extract_pdf_text(file_bytes: bytes) -> str:
    """Extract plain text from a PDF byte stream using PyMuPDF."""
    import fitz  # PyMuPDF

    parts: list[str] = []
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            parts.append(page.get_text())
    return "\n".join(parts)


def ingest_pdf(store: UserStore, file_bytes: bytes, filename: str) -> int:
    """Ingest an uploaded PDF. Same pipeline, tagged as a document."""
    text = extract_pdf_text(file_bytes)
    chunks = chunk_text(text)
    if not chunks:
        return 0
    vectors = embed(chunks)
    metadata = {"type": "document", "source": filename, "date": _now_iso()}
    return store.add(chunks, vectors, metadata)
