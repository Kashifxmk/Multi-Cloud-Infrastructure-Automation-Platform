from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app import app


def test_simulated_deployment_lifecycle():
    with TestClient(app) as client:
        client.post(
            "/api/auth/register",
            json={
                "full_name": "Deployment User",
                "email": f"deploy-{uuid4()}@example.com",
                "password": "local-password-123",
                "terms_accepted": True,
            },
        )
        response = client.post(
            "/api/deployments/plan",
            json={
                "name": "demo-stack",
                "configuration": {
                    "provider": "gcp",
                    "region": "asia-south1",
                    "vm_count": 2,
                    "machine_type": "e2-medium",
                    "vpc_cidr": "10.0.0.0/16",
                },
            },
        )
        assert response.status_code == 201
        deployment_id = response.json()["deployment"]["id"]
        assert response.json()["deployment"]["status"] == "awaiting-approval"
        approved = client.post(f"/api/deployments/{deployment_id}/approve")
        assert approved.status_code == 200
        assert approved.json()["deployment"]["status"] == "successful-simulated"
        assert len(approved.json()["deployment"]["resources"]) == 4
        destroyed = client.post(f"/api/deployments/{deployment_id}/destroy")
        assert destroyed.json()["status"] == "destroyed-simulated"
