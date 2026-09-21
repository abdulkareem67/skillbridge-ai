"""Database layer for SkillBridge AI.

The app runs on plain SQLite locally and on Postgres in production. Vercel's
filesystem is ephemeral, so a SQLite file there is wiped whenever the serverless
function cold-starts — which logged users out and lost their data. When a
Postgres connection string is present (Vercel Storage / Neon set POSTGRES_URL),
we use Postgres instead so accounts and data persist.

To avoid touching every router, a tiny wrapper gives a psycopg connection the
small slice of the sqlite3 API the routers rely on: ``conn.execute(sql, params)``
returning something with ``.fetchone()`` / ``.fetchall()`` / ``.lastrowid``,
plus ``conn.commit()`` and ``conn.close()``. The routers keep their SQLite-style
``?`` placeholders and ``INSERT OR IGNORE`` — this layer translates them.
"""
import os
import re
import secrets
import sqlite3
from pathlib import Path

# A Postgres connection string, if the host provides one. Vercel Storage / Neon
# expose it under one of these names.
DATABASE_URL = (
    os.environ.get("POSTGRES_URL")
    or os.environ.get("DATABASE_URL")
    or os.environ.get("POSTGRES_URL_NON_POOLING")
    or os.environ.get("POSTGRES_PRISMA_URL")
)
USE_POSTGRES = bool(DATABASE_URL)

# SQLite fallback for local development. The path can be overridden with
# SKILLBRIDGE_DB_PATH (used on read-only hosts where only /tmp is writable).
_default_db = Path(__file__).resolve().parent.parent / "data" / "skillbridge.db"
DB_PATH = Path(os.environ.get("SKILLBRIDGE_DB_PATH", str(_default_db)))
if not USE_POSTGRES:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- #
# Postgres compatibility shim
# --------------------------------------------------------------------------- #
def _to_postgres(sql: str) -> tuple[str, bool]:
    """Rewrite our SQLite-flavoured SQL for Postgres. Returns (sql, add_ignore)."""
    add_ignore = False
    if re.search(r"INSERT\s+OR\s+IGNORE", sql, flags=re.IGNORECASE):
        sql = re.sub(r"INSERT\s+OR\s+IGNORE", "INSERT", sql, flags=re.IGNORECASE)
        add_ignore = True
    # SQLite uses ? placeholders; psycopg uses %s. Our queries never contain a
    # literal '?', so a plain replace is safe.
    sql = sql.replace("?", "%s")
    return sql, add_ignore


class _PGCursor:
    def __init__(self, cur, lastrowid):
        self._cur = cur
        self.lastrowid = lastrowid

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()


class _PGConnection:
    """Adapts a psycopg connection to the sqlite3.Connection API the app uses."""

    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=()):
        from psycopg.rows import dict_row

        sql, add_ignore = _to_postgres(sql)
        stripped = sql.lstrip()
        is_insert = stripped[:6].upper() == "INSERT"
        has_conflict = "ON CONFLICT" in sql.upper()

        if is_insert and add_ignore and not has_conflict:
            sql = sql.rstrip().rstrip(";") + " ON CONFLICT DO NOTHING"

        # Emulate sqlite3's cursor.lastrowid via RETURNING id (every table has an
        # id column). Harmless on inserts whose id we never read.
        add_returning = is_insert and "RETURNING" not in sql.upper()
        if add_returning:
            sql = sql.rstrip().rstrip(";") + " RETURNING id"

        cur = self._conn.cursor(row_factory=dict_row)
        cur.execute(sql, params)

        lastrowid = None
        if add_returning:
            try:
                row = cur.fetchone()
                if row:
                    lastrowid = row.get("id")
            except Exception:
                lastrowid = None
        return _PGCursor(cur, lastrowid)

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


def connect():
    """Open a short-lived connection for a one-off query (outside a request)."""
    if USE_POSTGRES:
        import psycopg

        return _PGConnection(psycopg.connect(DATABASE_URL))
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def get_db():
    """FastAPI dependency: yields a per-request connection and closes it after."""
    if USE_POSTGRES:
        import psycopg

        conn = _PGConnection(psycopg.connect(DATABASE_URL))
        try:
            yield conn
        finally:
            conn.close()
        return

    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Schema
# --------------------------------------------------------------------------- #
_SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    location TEXT DEFAULT 'Pakistan',
    target_role TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill_name TEXT NOT NULL,
    category TEXT NOT NULL,
    source TEXT DEFAULT 'manual',
    UNIQUE(user_id, skill_name)
);

CREATE TABLE IF NOT EXISTS skill_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill_name TEXT NOT NULL,
    status TEXT DEFAULT 'not_started',
    UNIQUE(user_id, skill_name)
);

CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT UNIQUE NOT NULL,
    config_value TEXT NOT NULL
);
"""

_POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    location TEXT DEFAULT 'Pakistan',
    target_role TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS skills (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill_name TEXT NOT NULL,
    category TEXT NOT NULL,
    source TEXT DEFAULT 'manual',
    UNIQUE(user_id, skill_name)
);

CREATE TABLE IF NOT EXISTS skill_progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill_name TEXT NOT NULL,
    status TEXT DEFAULT 'not_started',
    UNIQUE(user_id, skill_name)
);

CREATE TABLE IF NOT EXISTS chat_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app_config (
    id SERIAL PRIMARY KEY,
    config_key TEXT UNIQUE NOT NULL,
    config_value TEXT NOT NULL
);
"""


SECRET_CONFIG_KEY = "session_secret"


def get_or_create_secret() -> str:
    """Return the session-signing secret held in the database.

    On first use a strong random secret is generated and stored, so the app is
    secure out of the box without anyone having to set an environment variable.
    Because it lives in the database it survives cold starts, which keeps users
    logged in — and it stays private, unlike a secret committed to the repo.
    """
    conn = connect()
    try:
        row = conn.execute(
            "SELECT config_value FROM app_config WHERE config_key = ?",
            (SECRET_CONFIG_KEY,),
        ).fetchone()
        if row:
            return row["config_value"]

        # Another cold start may be doing this at the same moment; whoever
        # inserts first wins and we both read back the same value.
        conn.execute(
            "INSERT OR IGNORE INTO app_config (config_key, config_value) VALUES (?, ?)",
            (SECRET_CONFIG_KEY, secrets.token_urlsafe(48)),
        )
        conn.commit()
        row = conn.execute(
            "SELECT config_value FROM app_config WHERE config_key = ?",
            (SECRET_CONFIG_KEY,),
        ).fetchone()
        return row["config_value"]
    finally:
        conn.close()


def init_db():
    if USE_POSTGRES:
        import psycopg

        conn = psycopg.connect(DATABASE_URL)
        try:
            with conn.cursor() as cur:
                for statement in _POSTGRES_SCHEMA.split(";"):
                    if statement.strip():
                        cur.execute(statement)
            conn.commit()
        finally:
            conn.close()
        return

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.executescript(_SQLITE_SCHEMA)
    conn.commit()
    conn.close()
