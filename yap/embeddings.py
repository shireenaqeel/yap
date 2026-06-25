"""Embedding model — loaded once and reused (it's expensive to construct)."""

from functools import lru_cache

import numpy as np

from . import config


@lru_cache(maxsize=1)
def _model():
    # Imported lazily so the rest of the app (and tests) don't pay the
    # sentence-transformers import cost unless embeddings are actually needed.
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(config.EMBED_MODEL)


def embed(texts: list[str]) -> np.ndarray:
    """Return L2-normalized float32 embeddings, shape (len(texts), EMBED_DIM).

    Normalizing means inner-product search (FAISS IndexFlatIP) == cosine
    similarity, which is what we want for retrieval.
    """
    vecs = _model().encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return vecs.astype("float32")
