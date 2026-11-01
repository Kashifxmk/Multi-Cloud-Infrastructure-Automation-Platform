from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app import app


def register(client: TestClient) -> None:
    client.post(
        "/api/auth/register",
        json={
            "full_name": "Account Owner",
            "email": f"account-{uuid4()}@example.com",
            "password": "local-password-123",
            "terms_accepted": True,
        },
    )


def test_simulated_account_lifecycle():
    with TestClient(app) as client:
        register(client)
        created = client.post(
            "/api/cloud-accounts",
            json={
                "provider": "aws",
                "display_name": "Demo AWS",
                "account_identifier": "123456789012",
            },
        )
        assert created.status_code == 201
        account_id = created.json()["account"]["id"]
        assert created.json()["account"]["status"] == "simulated-connected"
        assert client.post(f"/api/cloud-accounts/{account_id}/verify").status_code == 200
        assert len(client.get("/api/cloud-accounts").json()["accounts"]) == 1
        assert client.delete(f"/api/cloud-accounts/{account_id}").status_code == 204


def test_accounts_require_authentication():
    with TestClient(app) as client:
        assert client.get("/api/cloud-accounts").status_code == 401
        assert client.post(
            "/api/cloud-accounts",
            json={"provider": "gcp", "display_name": "Demo", "account_identifier": "project"},
        ).status_code == 401
