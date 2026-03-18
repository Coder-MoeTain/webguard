"""Integration tests for API endpoints."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    r = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    if r.status_code != 200:
        pytest.skip("Login failed")
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_health(client):
    """Health endpoint should return ok."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_login(client):
    """Login with demo credentials."""
    r = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200
    assert "access_token" in r.json()
    assert r.json()["username"] == "admin"


def test_login_invalid(client):
    """Invalid credentials should return 401."""
    r = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert r.status_code == 401


def test_datasets_list_requires_auth(client):
    """Datasets list should require auth."""
    r = client.get("/api/datasets/")
    assert r.status_code == 401


def test_datasets_list_with_auth(client, auth_headers):
    """Datasets list with auth should return list."""
    r = client.get("/api/datasets/", headers=auth_headers)
    assert r.status_code == 200
    assert "datasets" in r.json()


def test_models_list_requires_auth(client):
    """Models list should require auth."""
    r = client.get("/api/models/")
    assert r.status_code == 401


def test_models_list_with_auth(client, auth_headers):
    """Models list with auth should return list."""
    r = client.get("/api/models/", headers=auth_headers)
    assert r.status_code == 200
    assert "models" in r.json()


def test_training_list_requires_auth(client):
    """Training list should require auth."""
    r = client.get("/api/training/")
    assert r.status_code == 401


def test_training_list_with_auth(client, auth_headers):
    """Training list with auth should return jobs."""
    r = client.get("/api/training/", headers=auth_headers)
    assert r.status_code == 200
    assert "jobs" in r.json()


def test_training_ratio_validation(client, auth_headers):
    """Training start should reject invalid ratios."""
    r = client.post(
        "/api/training/start",
        headers=auth_headers,
        json={
            "data_path": "data/sample_sqli_37_features.parquet",
            "train_ratio": 0.5,
            "val_ratio": 0.5,
            "test_ratio": 0.5,
        },
    )
    assert r.status_code == 422


def test_preview_path_traversal_blocked(client, auth_headers):
    """Dataset preview should block path traversal."""
    r = client.get("/api/datasets/preview?path=../../../etc/passwd", headers=auth_headers)
    assert r.status_code == 400
    assert "data directory" in r.json().get("detail", "").lower()


def test_robustness_invalid_model_id(client, auth_headers):
    """Robustness should reject invalid model_id."""
    r = client.post(
        "/api/robustness/analyze",
        headers=auth_headers,
        json={
            "data_path": "data/sample_sqli_37_features.parquet",
            "model_id": "../../../etc/passwd",
        },
    )
    assert r.status_code in (400, 404)
