import os
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app import app


def test_admin_routes_enforce_backend_authorization():
    with TestClient(app) as client:
        client.post(
            "/api/auth/register",
            json={
                "full_name": "Regular User",
                "email": f"member-{uuid4()}@example.com",
                "password": "local-password-123",
                "terms_accepted": True,
            },
        )
        assert client.get("/api/admin/overview").status_code == 403


def test_admin_bootstrap_email_can_access_overview(monkeypatch):
    email = f"admin-{uuid4()}@example.com"
    monkeypatch.setenv("CLOUDPILOT_ADMIN_EMAIL", email)
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/register",
            json={
                "full_name": "Local Admin",
                "email": email,
                "password": "local-password-123",
                "terms_accepted": True,
            },
        )
        assert response.status_code == 201
        assert client.get("/api/admin/overview").status_code == 200
