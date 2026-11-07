from collections.abc import Collection

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import OrganizationMember, User


DEFAULT_MEMBER_ROLES = frozenset({"owner", "admin", "developer", "read-only"})


def organization_id_for_user(
    db: Session,
    user: User,
    allowed_roles: Collection[str] = DEFAULT_MEMBER_ROLES,
) -> str:
    statement = select(OrganizationMember).where(OrganizationMember.user_id == user.id)
    if allowed_roles:
        statement = statement.where(OrganizationMember.role.in_(allowed_roles))
    membership = db.scalar(statement)
    if not membership:
        raise HTTPException(status_code=403, detail="No organization membership found")
    return membership.organization_id
