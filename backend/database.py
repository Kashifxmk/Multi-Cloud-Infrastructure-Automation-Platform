import os
from collections.abc import Generator

from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


DATABASE_URL = os.getenv("CLOUDPILOT_DATABASE_URL", "sqlite:///./cloudpilot.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    admin_email = os.getenv("CLOUDPILOT_ADMIN_EMAIL", "").strip().lower()
    if admin_email:
        with SessionLocal() as db:
            user = db.scalar(select(models.User).where(models.User.email == admin_email))
            if user and not user.is_admin:
                user.is_admin = True
                db.commit()
