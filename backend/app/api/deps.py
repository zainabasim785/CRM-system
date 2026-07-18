"""FastAPI dependencies shared across API routers."""

from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.user import User
from app.services.auth_service import (
    AuthError,
    AuthService,
    InactiveUserError,
    InvalidTokenError,
    UserNotFoundError,
)
from app.services.conversation_service import ConversationService
from app.services.google_oauth_service import GoogleOAuthService
from app.services.reception_service import ReceptionService

bearer_scheme = HTTPBearer(auto_error=True)
optional_bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """Request-scoped SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_auth_service(db: Annotated[Session, Depends(get_db)]) -> AuthService:
    return AuthService(db)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    """Protected-route dependency — requires a valid Bearer JWT."""
    try:
        return auth_service.get_user_from_token(credentials.credentials)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found for this token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except InactiveUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_optional_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(optional_bearer_scheme),
    ],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User | None:
    """Optional auth — anonymous visitors allowed; invalid tokens still 401."""
    if credentials is None:
        return None
    return get_current_user(credentials, auth_service)


def get_conversation_service(
    db: Annotated[Session, Depends(get_db)],
) -> ConversationService:
    return ConversationService(db)


def get_reception_service(
    db: Annotated[Session, Depends(get_db)],
) -> ReceptionService:
    """Build per-request; AgentManager is resolved lazily inside the service."""
    return ReceptionService(db)


def get_google_oauth_service(
    db: Annotated[Session, Depends(get_db)],
) -> GoogleOAuthService:
    return GoogleOAuthService(db)


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]
DbSession = Annotated[Session, Depends(get_db)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
ConversationServiceDep = Annotated[ConversationService, Depends(get_conversation_service)]
ReceptionServiceDep = Annotated[ReceptionService, Depends(get_reception_service)]
GoogleOAuthServiceDep = Annotated[GoogleOAuthService, Depends(get_google_oauth_service)]
