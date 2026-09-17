import os
import sqlite3
from pathlib import Path

# The database file location can be overridden with the SKILLBRIDGE_DB_PATH env
# var. This is required on hosts with a read-only filesystem (e.g. Vercel), where
# only /tmp is writable.
_default_db = Path(__file__).resolve().parent.parent / "data" / "skillbridge.db"
DB_PATH = Path(os.environ.get("SKILLBRIDGE_DB_PATH", str(_default_db)))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.executescript(
        """
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
        """
    )
    conn.commit()
    conn.close()
