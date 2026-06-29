---
title: Yap
emoji: 💬
colorFrom: pink
colorTo: purple
sdk: streamlit
sdk_version: 1.48.1
app_file: app.py
pinned: false
short_description: A private journaling app with an AI that learns your patterns.
---

# 💬 Yap

A private journaling app where anyone can *yap* their thoughts and get a personal
AI that learns their own patterns over time. Most journaling apps just store
entries — Yap reflects your own patterns back to you, grounded only in your own
words.

Built for the **Girls Who Yap Fellowship 2.0** application.

## What it does

- **🔐 Accounts** — sign up / log in. Your data lives in the cloud, so it
  follows you across devices.
- **📝 Yap** — write a journal entry (tagged with a category like 💡 Idea or
  😤 Emotional rant), or upload a PDF. Everything runs through one pipeline:
  `extract → chunk → embed → store`.
- **🪞 Ask Yourself** — ask questions about yourself
  (*"What do I usually do when I'm overwhelmed?"*). Yap retrieves your most
  relevant past entries and answers **in your own voice, grounded only in what
  you've written** — no fabrication.
- **🎁 Personality Wrapped** — a Spotify-Wrapped-style AI recap of your week or
  month: top themes, mood arc, and a "personality this month" blurb that
  changes as you write more.
- **📊 Patterns** — most-mentioned topics, category breakdown, and journaling
  activity over the last *N* days.

## Tech stack

| Layer | Tool |
|------|------|
| Embeddings | `sentence-transformers` (all-MiniLM-L6-v2) |
| Database + vectors | Supabase Postgres + `pgvector` |
| Auth | username + bcrypt-hashed password |
| Generation | Groq API · Llama-3.1-8B |
| PDF extraction | PyMuPDF (`fitz`) |
| App | Streamlit |
| Charts | Plotly |

## Data architecture — per-user isolation

Everything lives in one shared Postgres database, but every query is scoped by
`user_id`, so one account can never read another's entries:

```
users    (id, username, password_hash, created_at)
entries  (id, user_id, text, embedding vector(384),
          type, category, source, created_at)
```

Typed entries are tagged `type='yap_entry'` (with a category), uploaded files
`type='document'`. Vector similarity search uses pgvector's cosine operator
(`embedding <=> query`), always filtered by `user_id` (`yap/storage.py`).

## Quick start

```bash
# 1. Install deps (a virtualenv is recommended)
pip install -r requirements.txt

# 2. Configure secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# then edit .streamlit/secrets.toml and set at least:
#   GROQ_API_KEY      -> https://console.groq.com/keys
#   SUPABASE_DB_URL   -> Supabase project: Settings > Database > Connection string
# The [auth] / [auth.google] section is optional — fill it in only to enable
# "Sign in with Google" (username + password works without it).

# 3. Run
streamlit run app.py
```

Tables are created automatically on first run. Open the local URL, sign up, and
start yapping.

## Project layout

```
app.py              Streamlit UI (auth + Yap / Ask Yourself / Wrapped / Patterns)
yap/
  config.py         env-driven settings + category list
  db.py             Postgres connection + schema (Supabase + pgvector)
  auth.py           signup / login (bcrypt)
  embeddings.py     cached MiniLM embedder
  storage.py        per-user reads/writes + vector search (isolation lives here)
  ingest.py         extract → chunk → embed → store (text + PDF)
  generation.py     retrieve + Groq Llama-3.1-8B answering
  wrapped.py        AI "Personality Wrapped" recap
  patterns.py       keyword / category / activity stats
```

## Deploy (Streamlit Community Cloud)

Push to GitHub, then at [share.streamlit.io](https://share.streamlit.io) point a
new app at this repo's `app.py`. Add `GROQ_API_KEY` and `SUPABASE_DB_URL` under
the app's **Secrets**. That gives you a public, shareable, cross-device link.

## Roadmap (stretch)

- 🎙️ Voice input (Whisper) for spoken yapping
- 🗓️ Weekly auto-generated recap
- 🏷️ Mood tagging per entry

---

Built by [Shireen Ansari](https://github.com/shireenaqeel).
