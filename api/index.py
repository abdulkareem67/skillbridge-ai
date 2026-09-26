"""Vercel serverless entrypoint for the SkillBridge AI FastAPI app.

Vercel's Python runtime looks for an ASGI app named `app` in this module.
The real application lives in ../backend/app/main.py, so we make that package
importable and re-export its `app`.
"""
import os
import sys
from pathlib import Path

# Make the backend package importable (backend/app -> `app` package).
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Production data lives in Postgres (Neon, connected through Vercel Storage);
# database.py picks it up from the environment. This SQLite path is only the
# fallback when no database is connected — /tmp is the one writable directory
# on Vercel, and it is wiped on cold starts, so main.py serves a setup page
# rather than running on it.
os.environ.setdefault("SKILLBRIDGE_DB_PATH", "/tmp/skillbridge.db")

from app.main import app  # noqa: E402  (import after sys.path/env setup)

# Expose `app` for Vercel's ASGI handler.
__all__ = ["app"]
