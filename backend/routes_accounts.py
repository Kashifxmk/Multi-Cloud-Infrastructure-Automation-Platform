from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .models import CloudAccount, OrganizationMember, User


router = APIRouter(prefix="/api/cloud-accounts", tags=["cloud accounts"])
SUPPORTED_PROVIDERS = {"aws", "gcp", "azure"}
SETUP_INSTRUCTIONS = {
    "aws": "Demo only: enter an AWS account label. Real IAM role verification will be added later.",
    "gcp": "Demo only: enter a GCP project label. Real workload identity verification will be added later.",
    "azure": "Demo only: enter an Azure subscription label. Real Entra verification will be added later.",
}


class CloudAccountRequest(BaseModel):
    provider: str
    display_name: str = Field(min_length=2, max_length=160)
    account_identifier: str = Field(min_length=2, max_length=160)


def organization_id_for_user(db: Session, user: User) -> str:
    membership = db.scalar(
        select(OrganizationMember).where(
            OrganizationMember.user_id == user.id,
            OrganizationMember.role.in_(["owner", "admin", "developer", "read-only"]),
        )
    )
    if not membership:
        raise HTTPException(status_code=403, detail="No organization membership found")
    return membership.organization_id


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
        status="simulated-connected",
        metadata_json={
            "account_identifier": request.account_identifier,
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
    account.status = "simulated-connected"
    account.metadata_json = {
        **account.metadata_json,
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "simulation": True,
    }
    db.commit()
    return {"mode": "simulated", "status": account.status, "message": "Simulated verification passed"}


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
