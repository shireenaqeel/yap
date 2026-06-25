"""Central configuration. Reads from environment (.env supported)."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Where every user's isolated folder lives: data/users/{user_id}/
DATA_DIR = Path(os.getenv("YAP_DATA_DIR", "data")) / "users"

# Models
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBED_DIM = 384  # all-MiniLM-L6-v2 output dimensionality

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# Ingest / retrieval tuning
CHUNK_SIZE = 600      # characters per chunk
CHUNK_OVERLAP = 100   # character overlap between consecutive chunks
TOP_K = 5             # chunks retrieved per question
