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

# On Vercel only /tmp is writable, so point the SQLite database there.
# NOTE: /tmp is ephemeral — data does not persist across cold starts.
os.environ.setdefault("SKILLBRIDGE_DB_PATH", "/tmp/skillbridge.db")

from app.main import app  # noqa: E402  (import after sys.path/env setup)

# Expose `app` for Vercel's ASGI handler.
__all__ = ["app"]
