# 💬 Yap

A private journaling app where anyone can *yap* their thoughts and get a personal
AI that learns their own patterns over time. Most journaling apps just store
entries — Yap reflects your own patterns back to you, grounded only in your own
words.

Built for the **Girls Who Yap Fellowship 2.0** application.

## What it does

- **📝 Yap** — write a journal entry (or upload a PDF like a resume or a
  "how I think" profile). Everything runs through one pipeline:
  `extract → chunk → embed → store`.
- **🪞 Ask Yourself** — ask questions about yourself
  (*"What do I usually do when I'm overwhelmed?"*). Yap retrieves your most
  relevant past entries and answers **in your own voice, grounded only in what
  you've written** — no fabrication.
- **📊 Patterns** — a lightweight recap: most-mentioned topics and journaling
  activity over the last *N* days.

## Tech stack

| Layer | Tool |
|------|------|
| Embeddings | `sentence-transformers` (all-MiniLM-L6-v2) |
| Vector store | FAISS (`IndexFlatIP`, per user) |
| Generation | Groq API · Llama-3.1-8B |
| PDF extraction | PyMuPDF (`fitz`) |
| App | Streamlit |
| Charts | Plotly |

## Data architecture — per-user isolation

FAISS stores only vectors, so each user gets two files kept in lockstep:

```
data/users/{user_id}/
    faiss_index.bin     ← vectors only
    chunks.jsonl        ← id → original text + metadata {type, source, date}
```

**Hard rule:** one `user_id`, one folder. No code path reads or writes across
folders — `user_id` is sanitized to a single safe path segment and the resolved
path is asserted to stay inside the data root (`yap/storage.py`). Typed entries
are tagged `type: "yap_entry"`, uploaded files `type: "document"`.

For the MVP, `user_id` is just a name typed once into `st.session_state` — the
folder isolation is what matters; real auth can be swapped in later without
touching anything else.

## Quick start

```bash
# 1. Install deps (a virtualenv is recommended)
pip install -r requirements.txt

# 2. Add your Groq key
cp .env.example .env        # then edit .env and paste your key
#   get a free key at https://console.groq.com/keys

# 3. Run
streamlit run app.py
```

Open the local URL Streamlit prints, type a name in the sidebar, and start
yapping. (Without a `GROQ_API_KEY`, ingest and Patterns still work — only the
"Ask Yourself" answering is disabled.)

## Project layout

```
app.py              Streamlit UI (Yap / Ask Yourself / Patterns tabs)
yap/
  config.py         env-driven settings
  embeddings.py     cached MiniLM embedder
  storage.py        per-user FAISS + chunks.jsonl (isolation lives here)
  ingest.py         extract → chunk → embed → store (text + PDF)
  generation.py     retrieve + Groq Llama-3.1-8B answering
  patterns.py       keyword / activity stats for the recap view
```

## Roadmap (stretch)

- 🎙️ Voice input (Whisper) for spoken yapping
- 🗓️ Weekly auto-generated recap
- 🏷️ Mood tagging per entry

---

Built by [Shireen Ansari](https://github.com/shireenaqeel).
