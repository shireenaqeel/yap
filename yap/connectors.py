"""Bring outside context into a user's space: GitHub projects, links, bio.

Everything flows through the same chunk -> embed -> store pipeline as journal
entries, just tagged differently, so "Ask Yourself" can answer about your
projects ("what have I built with Python?") grounded in your real repos.
"""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request

from .embeddings import embed
from .ingest import chunk_text
from .storage import UserStore

_API = "https://api.github.com"
_README_CHARS = 2500  # cap per-repo README so one big repo can't dominate


def _get(url: str, token: str | None = None) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "yap-app",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _repo_blob(username: str, repo: dict, token: str | None) -> str:
    parts = [f"GitHub project: {repo['name']}"]
    if repo.get("description"):
        parts.append(repo["description"])
    if repo.get("language"):
        parts.append(f"Primarily built with {repo['language']}.")
    topics = repo.get("topics") or []
    if topics:
        parts.append("Topics: " + ", ".join(topics))
    if repo.get("homepage"):
        parts.append(f"Live at: {repo['homepage']}")
    # README is the richest source of "what this project is" — best effort.
    try:
        rm = _get(f"{_API}/repos/{username}/{repo['name']}/readme", token)
        text = base64.b64decode(rm.get("content", "")).decode("utf-8", "ignore")
        if text.strip():
            parts.append(text[:_README_CHARS])
    except Exception:
        pass
    return "\n".join(parts)


def import_github(
    store: UserStore, username: str, max_repos: int = 12, token: str | None = None
) -> tuple[int, int]:
    """Fetch a user's public repos (most recently updated, non-fork) and ingest
    each as a 'github' entry. Returns (repos_imported, chunks_added)."""
    username = username.strip().lstrip("@")
    try:
        repos = _get(
            f"{_API}/users/{username}/repos?sort=updated&per_page=100", token
        )
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise ValueError(f"GitHub user '{username}' not found.") from e
        if e.code == 403:
            raise ValueError(
                "GitHub rate limit hit. Try again in a bit, or add a token."
            ) from e
        raise ValueError(f"Couldn't reach GitHub ({e.code}).") from e

    repos = [r for r in repos if not r.get("fork")][:max_repos]
    repos_done = 0
    chunks_added = 0
    for repo in repos:
        blob = _repo_blob(username, repo, token)
        chunks = chunk_text(blob)
        if not chunks:
            continue
        vectors = embed(chunks)
        chunks_added += store.add(
            chunks,
            vectors,
            {"type": "github", "source": f"github:{repo['name']}", "category": None},
        )
        repos_done += 1
    return repos_done, chunks_added
