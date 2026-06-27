"""Cloud database layer (Supabase Postgres + pgvector).

One shared connection per process, reused across Streamlit reruns. All vector
search and persistence lives here so the rest of the app never touches SQL.
"""

from __future__ import annotations

import threading

import psycopg
from pgvector.psycopg import register_vector

from . import config

_conn: psycopg.Connection | None = None
_lock = threading.Lock()

SCHEMA = """
create extension if not exists vector;

create table if not exists users (
    id            bigserial primary key,
    username      text unique not null,
    password_hash text not null,
    created_at    timestamptz not null default now()
);

create table if not exists entries (
    id         bigserial primary key,
    user_id    bigint not null references users(id) on delete cascade,
    text       text not null,
    embedding  vector(%d) not null,
    type       text not null default 'yap_entry',
    category   text,
    source     text,
    created_at timestamptz not null default now()
);

create index if not exists entries_user_idx on entries (user_id);
""" % config.EMBED_DIM


def get_conn() -> psycopg.Connection:
    """Return a live connection, (re)connecting if needed."""
    global _conn
    with _lock:
        if _conn is None or _conn.closed:
            if not config.DB_URL:
                raise RuntimeError(
                    "No SUPABASE_DB_URL configured. Add it to .env locally or "
                    "to Streamlit secrets when deployed."
                )
            # autocommit + no prepared statements => safe with any Supabase
            # connection-pooler mode.
            _conn = psycopg.connect(
                config.DB_URL, autocommit=True, prepare_threshold=None
            )
            # The pgvector extension must exist before its type can be
            # registered on the connection.
            _conn.execute("create extension if not exists vector")
            register_vector(_conn)
        return _conn


def init_schema() -> None:
    """Create tables/extension if they don't exist. Safe to call repeatedly."""
    with get_conn().cursor() as cur:
        cur.execute(SCHEMA)
