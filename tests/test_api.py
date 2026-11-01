from fastapi.testclient import TestClient

from backend.app import app


client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["mode"] == "local-demo"


def test_dashboard_uses_explicit_empty_state():
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    assert response.json()["mode"] == "demo"
    assert response.json()["metrics"]["monthly_spend"] is None


def test_validation_endpoint():
    response = client.post(
        "/api/config/validate",
        json={
            "config": {
                "project": {"name": "demo", "environment": "dev"},
                "cloud": {"provider": "gcp", "region": "asia-south1"},
            }
        },
    )
    assert response.status_code == 200
    assert response.json()["valid"] is True


def test_plan_preview_does_not_execute_terraform():
    response = client.post(
        "/api/terraform/plan-preview",
        json={
            "config": {
                "project": {"name": "demo", "environment": "dev"},
                "cloud": {"provider": "gcp", "region": "asia-south1"},
            }
        },
    )
    assert response.status_code == 200
    assert response.json()["mode"] == "preview"
