from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .models import (
    AuditLog,
    CloudAccount,
    Deployment,
    InfrastructureConfiguration,
    Organization,
    User,
)


router = APIRouter(prefix="/api/admin", tags=["admin"])


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Administrator access required")
    return user


@router.get("/overview")
def overview(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return {
        "mode": "local",
        "metrics": {
            "users": db.scalar(select(func.count(User.id))) or 0,
            "active_users": db.scalar(select(func.count(User.id)).where(User.is_active.is_(True))) or 0,
            "organizations": db.scalar(select(func.count(Organization.id))) or 0,
            "connected_accounts": db.scalar(select(func.count(CloudAccount.id))) or 0,
            "deployments": db.scalar(select(func.count(Deployment.id))) or 0,
            "configurations": db.scalar(select(func.count(InfrastructureConfiguration.id))) or 0,
        },
    }


@router.get("/users")
def users(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.scalars(select(User).order_by(User.created_at.desc())).all()
    return {
        "users": [
            {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "created_at": user.created_at,
            }
            for user in rows
        ]
    }


@router.get("/audit")
def audit(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(100)).all()
    return {
        "audit_logs": [
            {"id": row.id, "action": row.action, "details": row.details, "created_at": row.created_at}
            for row in rows
        ]
    }
