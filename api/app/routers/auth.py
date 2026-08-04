from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from ..config import get_settings
from ..deps import get_current_user, get_db
from ..models import User
from ..schemas import LoginIn, UserOut
from ..security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=UserOut)
def login(
    body: LoginIn, response: Response, db: OrmSession = Depends(get_db)
) -> User:
    user = db.scalar(select(User).where(User.username == body.username))
    if user is None or not verify_password(user.password_hash, body.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")

    settings = get_settings()
    response.set_cookie(
        key=settings.cookie_name,
        value=create_access_token(user.id),
        max_age=settings.access_token_ttl_min * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
    )
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    response.delete_cookie(get_settings().cookie_name, path="/")


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
