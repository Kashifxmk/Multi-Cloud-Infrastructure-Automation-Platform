import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .models import AuthToken, Organization, OrganizationMember, User, UserSession


logger = logging.getLogger(__name__)
password_hasher = PasswordHasher()
SESSION_COOKIE = "cloudpilot_session"
SESSION_DAYS = 7
FRONTEND_URL = os.getenv("CLOUDPILOT_FRONTEND_URL", "http://127.0.0.1:8080")


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(response: Response, user: User, db: Session) -> None:
    raw_token = secrets.token_urlsafe(32)
    session = UserSession(
        user_id=user.id,
        token_hash=token_digest(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS),
    )
    db.add(session)
    db.commit()
    response.set_cookie(
        SESSION_COOKIE,
        raw_token,
        max_age=SESSION_DAYS * 86400,
        httponly=True,
        secure=os.getenv("CLOUDPILOT_SECURE_COOKIES", "false").lower() == "true",
        samesite="lax",
    )


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    raw_token = request.cookies.get(SESSION_COOKIE)
    if not raw_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    session = db.scalar(
        select(UserSession).where(
            UserSession.token_hash == token_digest(raw_token),
            UserSession.expires_at > datetime.now(timezone.utc),
        )
    )
    if not session or not session.user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
    return session.user


def send_dev_email(kind: str, email: str, token: str) -> None:
    logger.info("DEVELOPMENT EMAIL %s for %s: %s/%s?token=%s", kind, email, FRONTEND_URL, kind, token)


def create_auth_token(db: Session, user: User, purpose: str) -> str:
    raw_token = secrets.token_urlsafe(32)
    db.add(
        AuthToken(
            user_id=user.id,
            token_hash=token_digest(raw_token),
            purpose=purpose,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
    )
    db.commit()
    return raw_token


def create_user(db: Session, full_name: str, email: str, password: str) -> User:
    normalized_email = email.strip().lower()
    if db.scalar(select(User).where(User.email == normalized_email)):
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = User(
        full_name=full_name.strip(),
        email=normalized_email,
        password_hash=hash_password(password),
        is_admin=normalized_email == os.getenv("CLOUDPILOT_ADMIN_EMAIL", "").strip().lower(),
    )
    organization = Organization(name=f"{full_name.strip()}'s workspace")
    db.add_all([user, organization])
    db.flush()
    db.add(OrganizationMember(user_id=user.id, organization_id=organization.id, role="owner"))
    db.commit()
    db.refresh(user)
    return user
