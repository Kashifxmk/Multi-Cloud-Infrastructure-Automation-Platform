from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app import app


def test_template_catalog_is_available():
    with TestClient(app) as client:
        response = client.get("/api/infrastructure/templates")
        assert response.status_code == 200
        assert len(response.json()["templates"]) == 6
        assert response.json()["mode"] == "local"


def test_configuration_requires_authentication_and_valid_fields():
    with TestClient(app) as client:
        payload = {
            "template_slug": "web-hosting",
            "configuration": {"provider": "gcp", "region": "asia-south1", "vm_count": 2, "vpc_cidr": "10.0.0.0/16"},
        }
        assert client.post("/api/infrastructure/configurations", json=payload).status_code == 401
        client.post(
            "/api/auth/register",
            json={
                "full_name": "Template User",
                "email": f"template-{uuid4()}@example.com",
                "password": "local-password-123",
                "terms_accepted": True,
            },
        )
        response = client.post("/api/infrastructure/configurations", json=payload)
        assert response.status_code == 201
        assert response.json()["configuration"]["template_slug"] == "web-hosting"
