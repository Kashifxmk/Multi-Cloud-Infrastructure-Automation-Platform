from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import (
    SESSION_COOKIE,
    create_session,
    create_user,
    get_current_user,
    hash_password,
    create_auth_token,
    send_dev_email,
    token_digest,
    verify_password,
)
from .database import get_db
from .models import AuthToken, User, UserSession
from .schemas import (
    LoginRequest,
    PasswordRequest,
    PasswordResetConfirmRequest,
    RegisterRequest,
    TokenRequest,
    UserResponse,
)


router = APIRouter(prefix="/api/auth", tags=["authentication"])


def user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        is_verified=user.is_verified,
        is_admin=user.is_admin,
    )


@router.post("/register", response_model=UserResponse, status_code=201)
def register(request: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    if not request.terms_accepted:
        raise HTTPException(status_code=422, detail="Terms acceptance is required")
    user = create_user(db, request.full_name, str(request.email), request.password)
    token = create_auth_token(db, user, "verify-email")
    send_dev_email("verify-email", user.email, token)
    create_session(response, user, db)
    return user_response(user)


@router.post("/login", response_model=UserResponse)
def login(request: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == str(request.email).lower()))
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    create_session(response, user, db)
    return user_response(user)


@router.post("/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    raw_token = request.cookies.get(SESSION_COOKIE)
    if raw_token:
        session = db.scalar(select(UserSession).where(UserSession.token_hash == token_digest(raw_token)))
        if session:
            db.delete(session)
            db.commit()
    response.delete_cookie(SESSION_COOKIE)


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user_response(user)


@router.post("/verify-email")
def verify_email(request: TokenRequest, db: Session = Depends(get_db)):
    auth_token = db.scalar(
        select(AuthToken).where(
            AuthToken.token_hash == token_digest(request.token),
            AuthToken.purpose == "verify-email",
            AuthToken.used_at.is_(None),
            AuthToken.expires_at > datetime.now(timezone.utc),
        )
    )
    if not auth_token:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")
    user = db.get(User, auth_token.user_id)
    user.is_verified = True
    auth_token.used_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Email verified"}


@router.post("/password-reset/request")
def request_password_reset(request: PasswordRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == str(request.email).lower()))
    if user:
        token = create_auth_token(db, user, "password-reset")
        send_dev_email("reset-password", user.email, token)
    return {"message": "If the account exists, a development reset link was logged"}


@router.post("/password-reset/confirm")
def confirm_password_reset(request: PasswordResetConfirmRequest, db: Session = Depends(get_db)):
    auth_token = db.scalar(
        select(AuthToken).where(
            AuthToken.token_hash == token_digest(request.token),
            AuthToken.purpose == "password-reset",
            AuthToken.used_at.is_(None),
            AuthToken.expires_at > datetime.now(timezone.utc),
        )
    )
    if not auth_token:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    user = db.get(User, auth_token.user_id)
    user.password_hash = hash_password(request.new_password)
    auth_token.used_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Password reset successfully"}
