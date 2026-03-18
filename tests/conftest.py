"""Pytest fixtures for WebGuard RF tests."""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Get auth headers after login."""
    r = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    if r.status_code != 200:
        pytest.skip("Login failed - demo auth may not be available")
    token = r.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}
