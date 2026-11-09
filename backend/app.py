from pathlib import Path
from typing import Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from pydantic import BaseModel, Field

from core.config_validator import validate_config
from core.provider_manager import terraform_directory
from .database import engine, init_db
from .routes_auth import router as auth_router
from .routes_accounts import router as accounts_router
from .routes_templates import router as templates_router
from .routes_pricing import router as pricing_router
from .routes_architecture import router as architecture_router
from .routes_terraform import router as terraform_router
from .routes_deployments import router as deployments_router
from .routes_admin import router as admin_router


ROOT = Path(__file__).resolve().parents[1]
@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="CloudPilot API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:5174",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(accounts_router)
app.include_router(templates_router)
app.include_router(pricing_router)
app.include_router(architecture_router)
app.include_router(terraform_router)
app.include_router(deployments_router)
app.include_router(admin_router)


class ValidationRequest(BaseModel):
    config: dict[str, Any] = Field(default_factory=dict)


@app.get("/api/health")
def health() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as error:
        raise HTTPException(status_code=503, detail="Database unavailable") from error
    return {"status": "ok", "mode": "local-demo", "database": "ok"}


@app.get("/api/demo/state")
def demo_state() -> dict[str, Any]:
    return {
        "mode": "demo",
        "message": "Mock state only; no cloud account is connected.",
        "provider": "gcp",
        "region": "asia-south1",
        "resources": [
            {"name": "cloudpilot-vpc", "type": "network", "status": "configured"},
            {"name": "cloudpilot-vm", "type": "compute", "status": "preview-only"},
        ],
    }


@app.get("/api/dashboard")
def dashboard() -> dict[str, Any]:
    return {
        "mode": "demo",
        "message": "Demo data only; connect a cloud account to show real metrics.",
        "metrics": {
            "cloud_accounts": 0,
            "deployments": 0,
            "active_resources": 0,
            "monthly_spend": None,
        },
        "provider_distribution": [],
        "recent_activity": [],
    }


@app.post("/api/config/validate")
def validate_configuration(request: ValidationRequest) -> dict[str, Any]:
    errors = validate_config(request.config)
    return {"valid": not errors, "errors": errors}


@app.post("/api/terraform/plan-preview")
def plan_preview(request: ValidationRequest) -> dict[str, Any]:
    errors = validate_config(request.config)
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})
    provider = request.config["cloud"]["provider"]
    directory = terraform_directory(provider, ROOT)
    return {
        "mode": "preview",
        "provider": provider,
        "terraform_directory": str(directory),
        "message": "Preview only. Terraform was not executed and no cloud API was called.",
    }
