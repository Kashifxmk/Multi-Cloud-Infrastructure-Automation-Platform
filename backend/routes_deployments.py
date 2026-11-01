import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .models import Deployment, DeploymentLog, DeploymentResource, OrganizationMember, User
from .terraform_generator import generate_files


router = APIRouter(prefix="/api/deployments", tags=["deployments"])
ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


class DeploymentRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    configuration: dict[str, Any]


def organization_id_for_user(db: Session, user: User) -> str:
    membership = db.scalar(select(OrganizationMember).where(OrganizationMember.user_id == user.id))
    if not membership:
        raise HTTPException(status_code=403, detail="No organization membership found")
    return membership.organization_id


def deployment_response(deployment: Deployment, resources: list[DeploymentResource]) -> dict[str, Any]:
    return {
        "id": deployment.id,
        "status": deployment.status,
        "provider": deployment.provider,
        "configuration": deployment.configuration,
        "resources": [
            {"name": resource.name, "type": resource.resource_type, "provider_id": resource.provider_id}
            for resource in resources
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
    return {"mode": "simulated", "message": "Plan ready for explicit approval.", "deployment": deployment_response(deployment, [])}


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
    report = deployment_response(deployment, resources)
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
