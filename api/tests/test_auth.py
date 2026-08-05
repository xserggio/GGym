"""Auth accepts the JWT via cookie (web) or Authorization: Bearer (native)."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

TEST_PASSWORD = "pw-test"  # matches conftest


def test_login_returns_token() -> None:
    resp = TestClient(app).post(
        "/auth/login", json={"username": "tester", "password": TEST_PASSWORD}
    )
    assert resp.status_code == 200
    assert resp.json()["token"]


def test_bearer_token_authenticates_without_cookie() -> None:
    token = (
        TestClient(app)
        .post("/auth/login", json={"username": "tester", "password": TEST_PASSWORD})
        .json()["token"]
    )

    fresh = TestClient(app)  # no cookie jar shared
    ok = fresh.get("/me/state", headers={"Authorization": f"Bearer {token}"})
    assert ok.status_code == 200

    assert fresh.get("/me/state").status_code == 401  # no cookie, no header


def test_garbage_bearer_is_rejected() -> None:
    resp = TestClient(app).get(
        "/me/state", headers={"Authorization": "Bearer not-a-jwt"}
    )
    assert resp.status_code == 401
