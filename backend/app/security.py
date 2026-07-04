"""Authentication and authorization helpers.

Issues and validates JWT bearer tokens and exposes FastAPI dependencies for
resolving the current user and enforcing admin-only access.
"""
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from . import crud, models
from .config import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, SECRET_KEY
from .db import get_db

# auto_error=False lets us return a clean 401 (rather than 403) when the
# Authorization header is missing.
_bearer_scheme = HTTPBearer(auto_error=False)

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def create_access_token(username: str) -> str:
    """Create a signed JWT for the given username."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """Resolve and return the authenticated user from the bearer token.

    The database is the source of truth for ``is_admin`` — we only trust the
    username from the token and re-read the user record.
    """
    if credentials is None or not credentials.credentials:
        raise _CREDENTIALS_EXCEPTION

    try:
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=[JWT_ALGORITHM]
        )
        username = payload.get("sub")
    except jwt.PyJWTError:
        raise _CREDENTIALS_EXCEPTION

    if not username:
        raise _CREDENTIALS_EXCEPTION

    user = crud.get_user(db, username)
    if user is None:
        raise _CREDENTIALS_EXCEPTION
    return user


def require_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    """Dependency that allows only admin users through."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user
