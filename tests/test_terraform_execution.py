from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app import app


def register(client: TestClient) -> None:
    client.post(
        "/api/auth/register",
        json={
            "full_name": "Plan Owner",
            "email": f"plan-{uuid4()}@example.com",
            "password": "local-password-123",
            "terms_accepted": True,
        },
    )


def test_plan_requires_real_verified_account(monkeypatch):
    monkeypatch.setenv("CLOUDPILOT_TERRAFORM_PLAN_ENABLED", "true")
    with TestClient(app) as client:
        register(client)
        account = client.post(
            "/api/cloud-accounts",
            json={
                "provider": "aws",
                "display_name": "Simulated AWS",
                "account_identifier": "123456789012",
            },
        ).json()["account"]
        response = client.post(
            "/api/terraform/plan",
            json={
                "account_id": account["id"],
                "configuration": {"provider": "aws", "region": "us-east-1"},
            },
        )

    assert response.status_code == 409
    assert "real verification" in response.json()["detail"]


def test_plan_requires_authentication(monkeypatch):
    monkeypatch.setenv("CLOUDPILOT_TERRAFORM_PLAN_ENABLED", "true")
    with TestClient(app) as client:
        response = client.post(
            "/api/terraform/plan",
            json={"account_id": "missing", "configuration": {"provider": "aws"}},
        )

    assert response.status_code == 401
