import json
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import SessionLocal, get_db
from .authorization import organization_id_for_user
from .models import CloudAccount, Deployment, DeploymentLog, DeploymentResource, User
from .terraform_execution import TerraformExecutionError, plan as terraform_plan
from .terraform_generator import generate_files
from .templates.schemas import validate_configuration


router = APIRouter(prefix="/api/deployments", tags=["deployments"])
ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


class DeploymentRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    configuration: dict[str, Any]


class TerraformDeploymentPlanRequest(BaseModel):
    account_id: str = Field(min_length=1)


def deployment_response(
    deployment: Deployment,
    resources: list[DeploymentResource],
    logs: list[DeploymentLog] | None = None,
) -> dict[str, Any]:
    return {
        "id": deployment.id,
        "status": deployment.status,
        "provider": deployment.provider,
        "configuration": deployment.configuration,
        "resources": [
            {"name": resource.name, "type": resource.resource_type, "provider_id": resource.provider_id}
            for resource in resources
        ],
        "logs": [
            {"id": log.id, "message": log.message, "level": log.level, "created_at": log.created_at}
            for log in (logs or [])
        ],
        "created_at": deployment.created_at,
    }


def get_owned_deployment(db: Session, deployment_id: str, user: User) -> Deployment:
    organization_id = organization_id_for_user(db, user)
    deployment = db.scalar(
        select(Deployment).where(
            Deployment.id == deployment_id,
            Deployment.organization_id == organization_id,
        )
    )
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return deployment


@router.get("")
def list_deployments(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    organization_id = organization_id_for_user(db, user)
    deployments = db.scalars(
        select(Deployment).where(Deployment.organization_id == organization_id).order_by(Deployment.created_at.desc())
    ).all()
    return {
        "mode": "simulated",
        "deployments": [
            deployment_response(
                item,
                db.scalars(select(DeploymentResource).where(DeploymentResource.deployment_id == item.id)).all(),
                db.scalars(
                    select(DeploymentLog)
                    .where(DeploymentLog.deployment_id == item.id)
                    .order_by(DeploymentLog.created_at.asc(), DeploymentLog.id.asc())
                ).all(),
            )
            for item in deployments
        ],
    }


@router.post("/plan", status_code=201)
def create_plan(
    request: DeploymentRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    configuration = request.configuration
    provider = configuration.get("provider")
    errors = validate_configuration(configuration.get("template_slug"), configuration)
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})
    try:
        generate_files(configuration)
    except (ValueError, KeyError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    organization_id = organization_id_for_user(db, user)
    deployment = Deployment(
        organization_id=organization_id,
        status="awaiting-approval",
        provider=provider,
        configuration={"name": request.name, **configuration},
    )
    db.add(deployment)
    db.flush()
    db.add(DeploymentLog(deployment_id=deployment.id, message="Local plan generated; awaiting approval."))
    db.commit()
    db.refresh(deployment)
    return {
        "mode": "simulated",
        "message": "Plan ready for explicit approval.",
        "deployment": deployment_response(
            deployment,
            [],
            db.scalars(select(DeploymentLog).where(DeploymentLog.deployment_id == deployment.id)).all(),
        ),
    }


@router.post("/{deployment_id}/approve")
def approve_deployment(
    deployment_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deployment = get_owned_deployment(db, deployment_id, user)
    if deployment.status != "awaiting-approval":
        raise HTTPException(status_code=409, detail="Deployment is not awaiting approval")
    deployment.status = "deploying-simulated"
    vm_count = int(deployment.configuration.get("vm_count", 1))
    resources = [
        DeploymentResource(
            deployment_id=deployment.id,
            name=f"{deployment.configuration.get('name', 'cloudpilot')}-vm-{index + 1}",
            resource_type="compute",
            provider_id=f"sim-{secrets.token_hex(6)}",
        )
        for index in range(vm_count)
    ]
    resources.extend(
        [
            DeploymentResource(
                deployment_id=deployment.id,
                name=f"{deployment.configuration.get('name', 'cloudpilot')}-network",
                resource_type="network",
                provider_id=f"sim-{secrets.token_hex(6)}",
            ),
            DeploymentResource(
                deployment_id=deployment.id,
                name=f"{deployment.configuration.get('name', 'cloudpilot')}-storage",
                resource_type="storage",
                provider_id=f"sim-{secrets.token_hex(6)}",
            ),
        ]
    )
    db.add_all(resources)
    deployment.status = "successful-simulated"
    db.add(DeploymentLog(deployment_id=deployment.id, message="Simulated resources created; no cloud API was called."))
    db.commit()
    db.refresh(deployment)
    report = deployment_response(
        deployment,
        resources,
        db.scalars(select(DeploymentLog).where(DeploymentLog.deployment_id == deployment.id)).all(),
    )
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / f"deployment-{deployment.id}.json").write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    return {"mode": "simulated", "message": "Deployment completed in simulation mode.", "deployment": report}


@router.post("/{deployment_id}/destroy")
def destroy_deployment(
    deployment_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deployment = get_owned_deployment(db, deployment_id, user)
    if deployment.status == "destroyed-simulated":
        raise HTTPException(status_code=409, detail="Deployment is already destroyed")
    deployment.status = "destroyed-simulated"
    db.add(DeploymentLog(deployment_id=deployment.id, message="Simulated destroy completed; no cloud resource was changed."))
    db.commit()
    return {"mode": "simulated", "status": deployment.status}


@router.post("/{deployment_id}/terraform-plan")
def execute_deployment_plan(
    deployment_id: str,
    request: TerraformDeploymentPlanRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deployment = get_owned_deployment(db, deployment_id, user)
    if deployment.status not in {"awaiting-approval", "plan-failed"}:
        raise HTTPException(status_code=409, detail="Deployment is not ready for Terraform planning")
    organization_id = organization_id_for_user(db, user)
    account = db.scalar(
        select(CloudAccount).where(
            CloudAccount.id == request.account_id,
            CloudAccount.organization_id == organization_id,
        )
    )
    if not account:
        raise HTTPException(status_code=404, detail="Cloud account not found")
    if account.provider != deployment.provider:
        raise HTTPException(status_code=422, detail="Cloud account provider does not match deployment")
    if account.status != "connected" or account.metadata_json.get("simulation") is not False:
        raise HTTPException(status_code=409, detail="Cloud account requires successful real verification")
    capability_errors = capability_preflight(account.metadata_json, deployment.configuration)
    if capability_errors:
        raise HTTPException(status_code=422, detail={"errors": capability_errors})

    deployment.status = "planning"
    db.add(DeploymentLog(deployment_id=deployment.id, message="Terraform plan started.", level="info"))
    db.commit()

    def persist_line(line: str) -> None:
        with SessionLocal() as stream_db:
            stream_db.add(DeploymentLog(deployment_id=deployment.id, message=line, level="info"))
            stream_db.commit()

    try:
        result = terraform_plan(deployment.configuration, on_output=persist_line)
    except (TerraformExecutionError, ValueError, KeyError) as error:
        deployment.status = "plan-failed"
        db.add(DeploymentLog(deployment_id=deployment.id, message=str(error), level="error"))
        db.commit()
        raise HTTPException(status_code=502, detail=str(error)) from error
    deployment.status = "plan-succeeded"
    db.add(DeploymentLog(deployment_id=deployment.id, message="Terraform plan completed; no resources were applied."))
    db.commit()
    return {"mode": "real-plan", "deployment_id": deployment.id, **result}


def capability_preflight(metadata: dict[str, Any], configuration: dict[str, Any]) -> list[str]:
    regions = metadata.get("regions")
    machine_types = metadata.get("machine_types")
    capabilities = metadata.get("capabilities")
    errors: list[str] = []
    if not isinstance(regions, list) or not regions:
        errors.append("Discover account capabilities before running a real plan.")
    elif configuration.get("region") not in regions:
        errors.append(f"Region '{configuration.get('region')}' is not available on this account.")
    if not isinstance(machine_types, list) or not machine_types:
        errors.append("Account machine type capabilities are unavailable.")
    elif configuration.get("machine_type") not in machine_types:
        errors.append(f"Machine type '{configuration.get('machine_type')}' is not available on this account.")
    if not isinstance(capabilities, list) or not {"network", "compute"}.issubset(capabilities):
        errors.append("Account does not advertise required network and compute capabilities.")
    return errors


@router.get("/{deployment_id}/logs")
def deployment_logs(
    deployment_id: str,
    after_id: str | None = Query(default=None, min_length=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deployment = get_owned_deployment(db, deployment_id, user)
    statement = (
        select(DeploymentLog)
        .where(DeploymentLog.deployment_id == deployment.id)
        .order_by(DeploymentLog.created_at.asc(), DeploymentLog.id.asc())
    )
    logs = db.scalars(statement).all()
    if after_id:
        log_ids = [log.id for log in logs]
        if after_id not in log_ids:
            raise HTTPException(status_code=400, detail="Unknown log cursor")
        logs = logs[log_ids.index(after_id) + 1 :]
    return {
        "deployment_id": deployment.id,
        "status": deployment.status,
        "logs": [
            {"id": log.id, "message": log.message, "level": log.level, "created_at": log.created_at}
            for log in logs
        ],
    }


@router.get("/{deployment_id}/logs/stream")
def deployment_log_stream(
    deployment_id: str,
    after_id: str | None = Query(default=None, min_length=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deployment = get_owned_deployment(db, deployment_id, user)
    if after_id:
        known = db.scalar(
            select(DeploymentLog).where(
                DeploymentLog.id == after_id,
                DeploymentLog.deployment_id == deployment.id,
            )
        )
        if not known:
            raise HTTPException(status_code=400, detail="Unknown log cursor")

    def events():
        cursor = after_id
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            with SessionLocal() as stream_db:
                statement = (
                    select(DeploymentLog)
                    .where(DeploymentLog.deployment_id == deployment_id)
                    .order_by(DeploymentLog.created_at.asc(), DeploymentLog.id.asc())
                )
                logs = stream_db.scalars(statement).all()
                if cursor:
                    ids = [log.id for log in logs]
                    logs = logs[ids.index(cursor) + 1 :] if cursor in ids else []
                for log in logs:
                    yield (
                        f"id: {log.id}\n"
                        f"event: log\n"
                        f"data: {json.dumps({'message': log.message, 'level': log.level, 'created_at': log.created_at}, default=str)}\n\n"
                    )
                    cursor = log.id
                current = stream_db.get(Deployment, deployment_id)
                if current and current.status not in {"awaiting-approval", "deploying-simulated"}:
                    yield f"event: complete\ndata: {json.dumps({'status': current.status})}\n\n"
                    return
            yield ": keep-alive\n\n"
            time.sleep(1)
        yield "event: timeout\ndata: {\"message\":\"Log stream timed out; resume with after_id.\"}\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
