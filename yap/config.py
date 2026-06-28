"""Central configuration. Reads from environment (.env locally, st.secrets in
the cloud). Streamlit secrets are merged into os.environ by db.py at startup.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# Cloud Postgres (Supabase) connection string. Required for the app to run.
DB_URL = os.getenv("SUPABASE_DB_URL", "")

# Models
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBED_DIM = 384  # all-MiniLM-L6-v2 output dimensionality

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
# Speech-to-text model (Groq-hosted Whisper) for voice yapping.
GROQ_WHISPER_MODEL = os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3-turbo")

# Ingest / retrieval tuning
CHUNK_SIZE = 600      # characters per chunk
CHUNK_OVERLAP = 100   # character overlap between consecutive chunks
TOP_K = 5             # chunks retrieved per question

# The fixed set of categories a user can tag a yap with.
CATEGORIES = [
    "💡 Idea",
    "😤 Emotional rant",
    "🎲 Random",
    "🎯 Goal",
    "🙏 Gratitude",
    "🪞 Reflection",
]
