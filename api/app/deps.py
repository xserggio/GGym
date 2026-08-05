"""FastAPI dependencies: DB session and the authenticated user."""
from __future__ import annotations

from collections.abc import Iterator

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session as OrmSession

from .config import get_settings
from .db import SessionLocal
from .models import User
from .security import decode_access_token


def get_db() -> Iterator[OrmSession]:
    with SessionLocal() as db:
        yield db


def _extract_token(request: Request) -> str | None:
    """Cookie (web/PWA) or `Authorization: Bearer` (native client)."""
    cookie = request.cookies.get(get_settings().cookie_name)
    if cookie:
        return cookie
    header = request.headers.get("Authorization")
    if header and header.lower().startswith("bearer "):
        return header[7:].strip() or None
    return None


def get_current_user(
    request: Request, db: OrmSession = Depends(get_db)
) -> User:
    token = _extract_token(request)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not authenticated")
    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid or expired token")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "user no longer exists")
    return user
