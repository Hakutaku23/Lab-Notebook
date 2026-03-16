from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User


def write_audit_log(
    db: Session,
    *,
    actor: User | None,
    action: str,
    resource_type: str,
    resource_id: UUID | None,
    summary: str,
    detail: dict | None = None,
) -> AuditLog:
    item = AuditLog(
        actor_id=actor.id if actor else None,
        actor_username=actor.username if actor else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        summary=summary,
        detail_json=detail,
    )
    db.add(item)
    db.flush()
    return item
