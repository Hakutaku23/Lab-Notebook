from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def resolve_user_id(db: Session, user_id: UUID | None) -> UUID:
    if user_id is not None:
        user = db.get(User, user_id)
        if user is None or not user.is_active:
            raise HTTPException(status_code=400, detail="指定用户不存在或不可用。")
        return user.id

    fallback_user = db.scalar(
        select(User)
        .where(User.is_active.is_(True))
        .order_by(User.created_at.asc())
    )
    if fallback_user is None:
        raise HTTPException(
            status_code=400,
            detail="未找到可用用户。请先执行 scripts/seed_dev_user.py。",
        )

    return fallback_user.id
