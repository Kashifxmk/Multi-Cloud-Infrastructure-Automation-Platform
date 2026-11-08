from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import get_current_user
from .authorization import organization_id_for_user
from .database import get_db
from .models import AuditLog, CloudAccount, User
from .terraform_execution import TerraformExecutionError, plan
from .terraform_generator import preview


router = APIRouter(prefix="/api/terraform", tags=["terraform"])


class TerraformRequest(BaseModel):
    provider: str
    region: str
    vm_count: int = Field(default=1, ge=1, le=100)
    machine_type: str = "e2-medium"
    vpc_cidr: str = "10.0.0.0/16"
    project_name: str = "cloudpilot"


class TerraformPlanRequest(BaseModel):
    account_id: str = Field(min_length=1)
    configuration: dict[str, Any]


@router.post("/generate-preview")
def generate_preview(request: TerraformRequest) -> dict[str, Any]:
    try:
        return preview(request.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/plan")
def execute_plan(
    request: TerraformPlanRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    organization_id = organization_id_for_user(db, user)
    account = db.scalar(
        select(CloudAccount).where(
            CloudAccount.id == request.account_id,
            CloudAccount.organization_id == organization_id,
        )
    )
    if not account:
        raise HTTPException(status_code=404, detail="Cloud account not found")
    configuration = request.configuration
    if configuration.get("provider") != account.provider:
        raise HTTPException(status_code=422, detail="Configuration provider does not match cloud account")
    if account.status != "connected" or account.metadata_json.get("simulation") is not False:
        raise HTTPException(status_code=409, detail="Cloud account requires successful real verification")
    try:
        result = plan(configuration)
    except (TerraformExecutionError, ValueError, KeyError) as error:
        db.add(
            AuditLog(
                organization_id=organization_id,
                user_id=user.id,
                action="terraform.plan.failed",
                details={"account_id": account.id, "provider": account.provider},
            )
        )
        db.commit()
        raise HTTPException(status_code=502, detail=str(error)) from error
    db.add(
        AuditLog(
            organization_id=organization_id,
            user_id=user.id,
            action="terraform.plan.completed",
            details={"account_id": account.id, "provider": account.provider},
        )
    )
    db.commit()
    return result
