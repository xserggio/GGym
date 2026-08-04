from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as OrmSession

from ..deps import get_current_user, get_db
from ..models import User
from ..schemas import SyncPush, SyncResult
from ..services import sync as sync_service

router = APIRouter(tags=["sync"])


@router.post("/sync", response_model=SyncResult)
def sync(
    push: SyncPush,
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> SyncResult:
    return sync_service.apply_and_pull(db, user, push)
