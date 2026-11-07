from datetime import datetime, timezone
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .authorization import organization_id_for_user
from .cloud.registry import SUPPORTED_PROVIDERS
from .cloud.verification import verify_account as verify_provider_account
from .models import CloudAccount, User


router = APIRouter(prefix="/api/cloud-accounts", tags=["cloud accounts"])
SETUP_INSTRUCTIONS = {
    "aws": "Simulation: enter an AWS account label. Production adapter will use read-only IAM role verification.",
    "gcp": "Simulation: enter a GCP project label. Production adapter will use workload identity verification.",
    "azure": "Simulation: enter an Azure subscription label. Production adapter will use Entra verification.",
}


class CloudAccountRequest(BaseModel):
    provider: str
    display_name: str = Field(min_length=2, max_length=160)
    account_identifier: str = Field(min_length=2, max_length=160)
    auth_method: Literal["default-chain", "profile", "role"] = "default-chain"
    role_arn: str | None = Field(default=None, max_length=2048)
    external_id: str | None = Field(default=None, max_length=256)
    profile: str | None = Field(default=None, max_length=128)


def serialize(account: CloudAccount) -> dict[str, Any]:
    return {
        "id": account.id,
        "provider": account.provider,
        "display_name": account.display_name,
        "status": account.status,
        "metadata": account.metadata_json,
        "created_at": account.created_at,
        "updated_at": account.updated_at,
    }


@router.get("/setup")
def setup_instructions():
    return {
        "mode": "simulated",
        "providers": [
            {"provider": provider, "instructions": instructions}
            for provider, instructions in SETUP_INSTRUCTIONS.items()
        ],
    }


@router.get("")
def list_accounts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    organization_id = organization_id_for_user(db, user)
    accounts = db.scalars(
        select(CloudAccount).where(CloudAccount.organization_id == organization_id)
    ).all()
    return {"mode": "simulated", "accounts": [serialize(account) for account in accounts]}


@router.post("", status_code=201)
def connect_account(
    request: CloudAccountRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    provider = request.provider.lower()
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=422, detail="Provider must be aws, gcp, or azure")
    organization_id = organization_id_for_user(db, user)
    account = CloudAccount(
        organization_id=organization_id,
        provider=provider,
        display_name=request.display_name,
        status=(
            "simulated-connected"
            if os.getenv("CLOUDPILOT_PROVIDER_MODE", "simulated").strip().lower() == "simulated"
            else "pending-verification"
        ),
        metadata_json={
            "account_identifier": request.account_identifier,
            "auth_method": request.auth_method,
            "auth_config": {
                key: value
                for key, value in {
                    "role_arn": request.role_arn,
                    "external_id": request.external_id,
                    "profile": request.profile,
                }.items()
                if value
            },
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "simulation": True,
        },
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return {"mode": "simulated", "account": serialize(account)}


@router.post("/{account_id}/verify")
def verify_account(
    account_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    organization_id = organization_id_for_user(db, user)
    account = db.scalar(
        select(CloudAccount).where(
            CloudAccount.id == account_id,
            CloudAccount.organization_id == organization_id,
        )
    )
    if not account:
        raise HTTPException(status_code=404, detail="Cloud account not found")
    account_identifier = str(account.metadata_json.get("account_identifier", ""))
    try:
        verification = verify_provider_account(
            account.provider,
            account_identifier,
            account.metadata_json.get("auth_config", {}),
        )
    except (RuntimeError, ValueError) as error:
        account.status = "verification-failed"
        db.commit()
        raise HTTPException(status_code=502, detail=str(error)) from error
    account.status = "simulated-connected" if verification["simulation"] else "connected"
    account.metadata_json = {
        **account.metadata_json,
        "identity": verification["identity"],
        "regions": verification["regions"],
        "capabilities": verification["capabilities"],
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "simulation": verification["simulation"],
    }
    db.commit()
    return {
        "mode": "simulated",
        "status": account.status,
        "message": "Simulated provider verification passed",
        "verification": verification,
    }


@router.delete("/{account_id}", status_code=204)
def disconnect_account(
    account_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    organization_id = organization_id_for_user(db, user)
    account = db.scalar(
        select(CloudAccount).where(
            CloudAccount.id == account_id,
            CloudAccount.organization_id == organization_id,
        )
    )
    if not account:
        raise HTTPException(status_code=404, detail="Cloud account not found")
    db.delete(account)
    db.commit()
