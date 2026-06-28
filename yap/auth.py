"""Account signup / login. Passwords are bcrypt-hashed; we never store the
plain text. A logged-in user is represented simply by their integer id.
"""

from __future__ import annotations

import bcrypt

from .db import get_conn


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _check(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False


def sign_up(username: str, password: str) -> int:
    """Create a new account. Returns the new user id. Raises ValueError on
    bad input or if the username is taken."""
    username = username.strip().lower()
    if len(username) < 3:
        raise ValueError("Username must be at least 3 characters.")
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters.")

    with get_conn().cursor() as cur:
        cur.execute("select 1 from users where username = %s", (username,))
        if cur.fetchone():
            raise ValueError("That username is already taken.")
        cur.execute(
            "insert into users (username, password_hash) values (%s, %s) "
            "returning id",
            (username, _hash(password)),
        )
        return cur.fetchone()[0]


def log_in(username: str, password: str) -> int:
    """Verify credentials. Returns the user id, or raises ValueError."""
    username = username.strip().lower()
    with get_conn().cursor() as cur:
        cur.execute(
            "select id, password_hash from users where username = %s",
            (username,),
        )
        row = cur.fetchone()
    if not row or row[1] is None or not _check(password, row[1]):
        # row[1] is None for Google accounts — they must use "Sign in with Google".
        raise ValueError("Wrong username or password.")
    return row[0]


def get_theme(user_id: int) -> str | None:
    """Return the user's saved aesthetic theme, or None if they haven't set one."""
    with get_conn().cursor() as cur:
        cur.execute("select theme from users where id = %s", (user_id,))
        row = cur.fetchone()
    return row[0] if row else None


def set_theme(user_id: int, theme: str) -> None:
    """Persist the user's chosen aesthetic theme."""
    with get_conn().cursor() as cur:
        cur.execute("update users set theme = %s where id = %s", (theme, user_id))


def get_or_create_oauth_user(email: str, provider: str = "google") -> int:
    """Look up (or create) an account for a verified OAuth identity. The user's
    email becomes their username; no password is stored."""
    email = email.strip().lower()
    with get_conn().cursor() as cur:
        cur.execute("select id from users where username = %s", (email,))
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute(
            "insert into users (username, password_hash, provider) "
            "values (%s, NULL, %s) returning id",
            (email, provider),
        )
        return cur.fetchone()[0]
