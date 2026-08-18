from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session as OrmSession

from ..config import get_settings
from ..deps import get_current_user, get_db
from ..models import PushSubscription, User
from ..schemas import NotificationIn, NotificationOut, PushSubscriptionIn
from ..services import notifications

router = APIRouter(prefix="/me/notifications", tags=["notifications"])


def _out(db: OrmSession, user: User) -> NotificationOut:
    setting = notifications.get_or_create_settings(db, user.id)
    devices = db.scalar(
        select(func.count())
        .select_from(PushSubscription)
        .where(PushSubscription.user_id == user.id)
    )
    return NotificationOut(
        enabled=setting.enabled,
        hour=setting.hour,
        minute=setting.minute,
        vapid_public_key=get_settings().vapid_public_key,
        devices=devices or 0,
    )


@router.get("", response_model=NotificationOut)
def read(
    user: User = Depends(get_current_user), db: OrmSession = Depends(get_db)
) -> NotificationOut:
    out = _out(db, user)
    db.commit()
    return out


@router.patch("", response_model=NotificationOut)
def update(
    payload: NotificationIn,
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> NotificationOut:
    setting = notifications.get_or_create_settings(db, user.id)
    setting.enabled = payload.enabled
    setting.hour = payload.hour
    setting.minute = payload.minute
    # Changing the time re-arms today's reminder instead of waiting a day.
    setting.last_sent_on = None
    db.flush()
    out = _out(db, user)
    db.commit()
    return out


@router.post("/subscribe", response_model=NotificationOut)
def subscribe(
    payload: PushSubscriptionIn,
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> NotificationOut:
    notifications.subscribe(
        db, user, payload.endpoint, payload.keys.p256dh, payload.keys.auth
    )
    out = _out(db, user)
    db.commit()
    return out


@router.delete("/subscribe", status_code=status.HTTP_204_NO_CONTENT)
def unsubscribe(
    endpoint: str,
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> Response:
    sub = db.scalar(
        select(PushSubscription).where(
            PushSubscription.endpoint == endpoint,
            PushSubscription.user_id == user.id,
        )
    )
    if sub is not None:
        db.delete(sub)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
