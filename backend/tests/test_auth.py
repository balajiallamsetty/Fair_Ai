"""Auth flow tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.core.database import get_database
from backend.app.core.security import get_current_user
from backend.app.main import app


def test_register_and_login(fake_db):
    """Registering and logging in a user should return a JWT and user payload."""

    app.dependency_overrides[get_database] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: None
    client = TestClient(app)

    register_response = client.post(
        "/api/v1/governance/auth/register",
        json={
            "email": "alice@example.com",
            "full_name": "Alice Example",
            "password": "StrongPass123!",
            "role": "user",
        },
    )
    assert register_response.status_code == 200
    assert register_response.json()["email"] == "alice@example.com"

    login_response = client.post(
        "/api/v1/governance/auth/login",
        json={"email": "alice@example.com", "password": "StrongPass123!"},
    )
    assert login_response.status_code == 200
    body = login_response.json()
    assert body["access_token"]
    assert body["user"]["email"] == "alice@example.com"

    app.dependency_overrides.clear()
