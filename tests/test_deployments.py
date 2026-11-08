from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app import app
from backend.database import SessionLocal
from backend.models import CloudAccount


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


def test_deployment_logs_support_cursor_retrieval():
    with TestClient(app) as client:
        client.post(
            "/api/auth/register",
            json={
                "full_name": "Log User",
                "email": f"logs-{uuid4()}@example.com",
                "password": "local-password-123",
                "terms_accepted": True,
            },
        )
        response = client.post(
            "/api/deployments/plan",
            json={
                "name": "log-test",
                "configuration": {
                    "provider": "gcp",
                    "region": "asia-south1",
                    "vm_count": 1,
                    "machine_type": "e2-medium",
                    "vpc_cidr": "10.0.0.0/16",
                },
            },
        )
        deployment = response.json()["deployment"]
        first_log = deployment["logs"][0]

        logs = client.get(f"/api/deployments/{deployment['id']}/logs")
        assert logs.status_code == 200
        assert logs.json()["logs"][0]["id"] == first_log["id"]
        empty = client.get(
            f"/api/deployments/{deployment['id']}/logs?after_id={first_log['id']}"
        )
        assert empty.status_code == 200
        assert empty.json()["logs"] == []


def test_deployment_logs_require_authentication():
    with TestClient(app) as client:
        response = client.get("/api/deployments/missing/logs")

    assert response.status_code == 401


def test_deployment_log_stream_emits_completion():
    with TestClient(app) as client:
        client.post(
            "/api/auth/register",
            json={
                "full_name": "Stream User",
                "email": f"stream-{uuid4()}@example.com",
                "password": "local-password-123",
                "terms_accepted": True,
            },
        )
        planned = client.post(
            "/api/deployments/plan",
            json={
                "name": "stream-test",
                "configuration": {
                    "provider": "gcp",
                    "region": "asia-south1",
                    "vm_count": 1,
                    "machine_type": "e2-medium",
                    "vpc_cidr": "10.0.0.0/16",
                },
            },
        )
        deployment_id = planned.json()["deployment"]["id"]
        client.post(f"/api/deployments/{deployment_id}/approve")

        with client.stream("GET", f"/api/deployments/{deployment_id}/logs/stream") as stream:
            body = "".join(stream.iter_text())

    assert "event: log" in body
    assert "event: complete" in body


def test_terraform_plan_job_persists_output(monkeypatch):
    from backend import routes_deployments

    def fake_plan(configuration, on_output=None):
        assert configuration["provider"] == "gcp"
        assert on_output is not None
        on_output("Plan: 2 to add, 0 to change, 0 to destroy.")
        return {"mode": "real-plan", "message": "done", "output": "Plan: 2 to add"}

    monkeypatch.setattr(routes_deployments, "terraform_plan", fake_plan)
    with TestClient(app) as client:
        client.post(
            "/api/auth/register",
            json={
                "full_name": "Plan Job User",
                "email": f"plan-job-{uuid4()}@example.com",
                "password": "local-password-123",
                "terms_accepted": True,
            },
        )
        account = client.post(
            "/api/cloud-accounts",
            json={
                "provider": "gcp",
                "display_name": "Real GCP",
                "account_identifier": "project-id",
            },
        ).json()["account"]
        with SessionLocal() as db:
            cloud_account = db.scalar(select(CloudAccount).where(CloudAccount.id == account["id"]))
            cloud_account.status = "connected"
            cloud_account.metadata_json = {
                "simulation": False,
                "regions": ["asia-south1"],
                "machine_types": ["e2-medium"],
                "capabilities": ["network", "compute"],
            }
            db.commit()
        planned = client.post(
            "/api/deployments/plan",
            json={
                "name": "real-plan-job",
                "configuration": {
                    "provider": "gcp",
                    "region": "asia-south1",
                    "vm_count": 1,
                    "machine_type": "e2-medium",
                    "vpc_cidr": "10.0.0.0/16",
                },
            },
        )
        deployment_id = planned.json()["deployment"]["id"]
        response = client.post(
            f"/api/deployments/{deployment_id}/terraform-plan",
            json={"account_id": account["id"]},
        )
        logs = client.get(f"/api/deployments/{deployment_id}/logs").json()["logs"]

    assert response.status_code == 200
    assert response.json()["mode"] == "real-plan"
    assert response.json()["deployment_id"] == deployment_id
    assert any("2 to add" in log["message"] for log in logs)
