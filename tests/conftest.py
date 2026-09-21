"""Shared test setup.

The app reads its database location from the environment at import time, so the
environment is prepared *before* ``app.main`` is imported — otherwise the tests
would run against the developer's real SQLite file, or against production
Postgres if a connection string happens to be exported.
"""
import os
import sys
import tempfile
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))


@pytest.fixture(scope="session")
def client():
    """A TestClient wired to a throwaway SQLite database."""
    db_path = Path(tempfile.gettempdir()) / f"skillbridge-test-{uuid.uuid4().hex}.db"
    os.environ["SKILLBRIDGE_DB_PATH"] = str(db_path)

    # Force the local SQLite path: drop the production markers and any variable
    # holding a Postgres URL, whatever prefix the host gave it.
    os.environ.pop("VERCEL", None)
    os.environ.pop("SKILLBRIDGE_SECRET", None)
    for key, value in list(os.environ.items()):
        if isinstance(value, str) and value.startswith(("postgres://", "postgresql://")):
            os.environ.pop(key, None)

    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client

    for suffix in ("", "-wal", "-shm"):
        Path(str(db_path) + suffix).unlink(missing_ok=True)


@pytest.fixture(scope="session")
def account(client):
    """Register one user for the whole run and leave the session signed in."""
    credentials = {
        "name": "Smoke Test",
        "email": f"smoke-{uuid.uuid4().hex[:12]}@example.com",
        "password": "smoke-test-pw-123",
        "location": "Lahore",
    }
    response = client.post("/api/auth/register", json=credentials)
    assert response.status_code == 200, response.text
    return credentials
