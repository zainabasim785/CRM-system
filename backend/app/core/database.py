"""
SQLAlchemy 2.0 engine and session factory.

Provides:
- `engine` — connection pool to PostgreSQL (Supabase or local)
- `SessionLocal` — session factory for request / worker scopes
- `get_db` — FastAPI dependency yielding a request-scoped session
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=settings.db_pool_pre_ping,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    """Yield a DB session and always close it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
