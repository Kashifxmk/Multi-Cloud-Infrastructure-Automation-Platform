from fastapi.testclient import TestClient
from uuid import uuid4

from backend.app import app


def test_registration_session_profile_and_logout():
    email = f"local-user-{uuid4()}@example.com"
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/register",
            json={
                "full_name": "Local User",
                "email": email,
                "password": "local-password-123",
                "terms_accepted": True,
            },
        )
        assert response.status_code == 201
        assert "cloudpilot_session=" in response.headers["set-cookie"]
        assert client.get("/api/auth/me").status_code == 200
        assert client.post("/api/auth/logout").status_code == 204
        assert client.get("/api/auth/me").status_code == 401


def test_invalid_login_is_rejected():
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/login",
            json={"email": "missing@example.com", "password": "wrong-password"},
        )
        assert response.status_code == 401
